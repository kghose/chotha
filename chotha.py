import datetime, apsw, markdown2 as markdown, bottle, re, logging, pubmed, ConfigParser
from bottle import route, debug, template, request, validate, send_file, error

#Config file
config = ConfigParser.RawConfigParser()

#database name
dbname = None

#set up logging
logger = logging.getLogger('chotha')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)

def dbq(query, bindings = [], many = False, conn = None):
  """Utility function to handle db queries. Based on query type, the function
  returns last rowid or rows (which is a list of dictionaries)"""
  
  #Get the first word of the query to figure out what we should return
  cmd = query.split(' ',1)[0].upper()
  
  if conn == None:
    conn = apsw.Connection(dbname)
  c = conn.cursor()
  if many:
    c.executemany(query, bindings)
  else:
    c.execute(query, bindings)
  if cmd == 'SELECT':
    try:
      col_names = c.getdescription()
    except:
      pass #Just means returned no rows
    rows_in = c.fetchall()
    rows_out = []
    for row_in in rows_in:
      row_out = {}
      for c in range(len(col_names)):
        row_out[col_names[c][0]] = row_in[c]
      rows_out.append(row_out)
    return rows_out
  if cmd == 'INSERT':
    return conn.last_insert_rowid()

def get_source_fields(include_column_type = False):
  """Need an ordered list that starts with id. INSERT and UPDATE operations
  require us to treat the id differently compared to regular fields."""
  source_fields = [
  ['id','INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL'],
  ['abstract', 'TEXT'],
  ['address','VARCHAR(255)'],
  ['author','VARCHAR(255)'],
  ['booktitle','VARCHAR(255)'],
  ['chapter','VARCHAR(255)'],
  ['citekey','VARCHAR(255)'],
  ['created_at','DATETIME'],
  ['doi','VARCHAR(255)'],
  ['edition','VARCHAR(255)'],
  ['editor','VARCHAR(255)'],
  ['howpublished','VARCHAR(255)'],
  ['institution','VARCHAR(255)'],
  ['journal','VARCHAR(255)'],
  ['month','VARCHAR(255)'],
  ['note_id', 'INTEGER'],
  ['number','VARCHAR(255)'],
  ['organization','VARCHAR(255)'],
  ['pages','VARCHAR(255)'],
  ['publisher','VARCHAR(255)'],
  ['school','VARCHAR(255)'],
  ['series','VARCHAR(255)'],
  ['title','VARCHAR(255)'],
  ['source_type','VARCHAR(255)'],
  ['volume','VARCHAR(255)'],
  ['year','INTEGER']
  ]
  if include_column_type:
    return source_fields
  else:
    return [source_fields[n][0] for n in range(len(source_fields))]

def get_empty_source():
  """Return us a dummy source dictionary with the fields filled out with NULLS."""
  sfs = get_source_fields()
  source = {}
  for f in sfs:
    source[f] = '' 
  return source

def create_database():
  """Creates a new empty database."""
  #Always start with id  
  dbq('CREATE TABLE "notes" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "title" VARCHAR(255) DEFAULT "A title", "date" DATETIME, "body" TEXT DEFAULT "A body", "key_list" VARCHAR(255) DEFAULT "", "source_id" INTEGER)')
  source_fields = get_source_fields(include_column_type=True)
  query = 'CREATE TABLE "sources" ('
  query += '"%s" %s' %(source_fields[0][0], source_fields[0][1]) 
  for n in range(1,len(source_fields)):
    query += ', "%s" %s' %(source_fields[n][0], source_fields[n][1])
  query += ')'
  dbq(query)
  dbq('CREATE TABLE "keywords" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "name" VARCHAR(255))')  
  dbq('CREATE TABLE "keywords_notes" ("keyword_id" INTEGER, "note_id" INTEGER, PRIMARY KEY (keyword_id, note_id))')
  trigger = \
  """CREATE TRIGGER notesource1 
  AFTER UPDATE OF title ON sources 
  BEGIN
    UPDATE notes SET title = new.title || ' (' || new.citekey || ')' WHERE source_id = new.id;
  END"""
  dbq(trigger)
  trigger = \
  """CREATE TRIGGER notesource2 
  AFTER UPDATE OF citekey ON sources 
  BEGIN
    UPDATE notes SET title = new.title || ' (' || new.citekey || ')' WHERE source_id = new.id;
  END"""
  dbq(trigger)

#Keyword ops -------------------------------------------------------------------
def cskeystring_to_list(cskeystring):
  keyword_strings = cskeystring.split(',')
  keywords = []
  for name in keyword_strings:
    name = name.strip()
    if name == '':#Ignore blanks
      continue
    keywords.append(name)
  return keywords

def find_or_create_keywords(keywords):
  """Find or create keywords in a list and return the keyword id."""
  kids = []
  for keyword in keywords:
    name = keyword.strip()
    row = dbq('SELECT id FROM keywords WHERE name LIKE ?', (name,))
    if len(row) == 0:
      id = dbq('INSERT INTO keywords (name) VALUES (?)', (name,))
    else:
      id = row[0]['id']
    kids.append(id)
  return kids

def save_note_keywords(note):
  """Keywords are a comma separated list, we first extract that."""

  note_id = note['id']    
  #Delete original list
  dbq('DELETE FROM keywords_notes WHERE note_id=?', (note_id,))
  #Create new list
  keywords = cskeystring_to_list(note['key_list'])
  new_kids = find_or_create_keywords(keywords)
  if len(new_kids) > 0:
    bindings = []
    for kid in new_kids:
      bindings.append([kid, note_id])
    dbq('INSERT INTO keywords_notes (keyword_id,note_id) VALUES (?,?)', 
        bindings, many=True)
  #Clean up unused keywords
  dbq('DELETE FROM keywords WHERE id NOT IN (SELECT keyword_id FROM keywords_notes)')
  

#TODO fix to remove references to sources
def fetch_conjunction_candidates(keywords = []):
  """Given the keyword, fetch a list of keywords that appear in conjunction
  with it in the database in notes and sources.
  
  Important SQL snippets:
  -> This allows us to do keyword intersection (also see below)
  SELECT kn.note_id FROM keywords_notes AS kn 
    WHERE kn.keyword_id IN 
    (SELECT k.id FROM keywords k WHERE %s) <-put in the keyword clause here
    GROUP BY kn.note_id HAVING COUNT(*) = %d
  
  -> return all the keywords attached to these notes
  SELECT DISTINCT kn.keyword_id FROM keywords_notes kn WHERE kn.note_id IN ...
  
  -> final SQL (to incorporate both notes and sources)
  SELECT k.name FROM keywords k WHERE k.id IN
   (SELECT DISTINCT kn.keyword_id FROM keywords k, keywords_notes kn WHERE kn.note_id IN
     (SELECT kn.note_id FROM keywords_notes AS kn WHERE kn.keyword_id IN 
       (SELECT k.id FROM keywords k WHERE ?) <-put in the keyword clause here
        GROUP BY kn.note_id HAVING COUNT(*) = ?) <- no of keywords
   UNION
   SELECT DISTINCT ks.keyword_id FROM keywords k, keywords_sources ks WHERE ks.source_id IN
     (SELECT ks.source_id FROM keywords_sources AS ks WHERE ks.keyword_id IN 
       (SELECT k.id FROM keywords k WHERE ?) <-put in the keyword clause here
        GROUP BY ks.source_id HAVING COUNT(*) = ?)) <- no of keywords   
  AND k.id NOT IN (SELECT k.id FROM keywords k WHERE ?) <-put in the keyword clause here
      
  """
  arg_list = []
  if len(keywords) > 0:
    kq = ' k.name=? ' 
    for n in range(1,len(keywords)):
      kq += ' OR k.name=? ' 
    
    query = \
    'SELECT k.name FROM keywords k WHERE k.id IN \
      (SELECT DISTINCT kn.keyword_id FROM keywords k, keywords_notes kn WHERE kn.note_id IN \
        (SELECT kn.note_id FROM keywords_notes AS kn WHERE kn.keyword_id IN \
         (SELECT k.id FROM keywords k WHERE %s) \
         GROUP BY kn.note_id HAVING COUNT(*) = ?)) \
     AND k.id NOT IN (SELECT k.id FROM keywords k WHERE %s) ORDER BY k.name ASC' %(kq,kq)
    arg_list = keywords + [len(keywords)] + keywords
  else:
    query = 'SELECT k.name FROM keywords k ORDER BY k.name ASC'
  return dbq(query, arg_list)

# Note ops ---------------------------------------------------------------------
def create_new_note(note):
  note['date'] = datetime.datetime.now().isoformat()
  fields = note.keys()
  query = 'INSERT INTO notes ('
  query += fields[0]
  for n in range(1,len(fields)):
    query += ', ' + fields[n]
  query += ') VALUES (?'
  for n in range(1,len(fields)):
    query += ',?'
  query += ')'
  bindings = []
  for n in range(len(fields)):
    bindings.append(note[fields[n]])
  note['id'] = dbq(query, bindings)  
  save_note_keywords(note)
  return note

def save_note(note):
  """We then refetch the saved note so we can display it."""
  dbq("UPDATE notes SET date = ?, title = ?, body = ?, key_list = ? WHERE id LIKE ?", 
      (note['date'], note['title'], note['body'], note['key_list'], note['id']))
  save_note_keywords(note)

#TODO handle flag for sources
def parse_notes(rows_in):
  """Given a list of row objects returned by a fetch, copy the data into a new
  dictionary after running each entry through the markdown parser."""

  md = markdown.markdown #To save time
  pnote = re.compile(r'\[(.+?)\]\[note:(\d+?)\]')#For the wiki links substitution.
  
  def nice_date(date):
    nd = datetime.date(int(date[0:4]),int(date[5:7]),int(date[8:10]))
    return nd.strftime('%a %b %d, %Y')
  
  def format_body(body):
    def linx(match):
      return '<a href="/note/%s">%s</a>' %(match.group(2),match.group(1))
      
    text = pnote.sub(linx, body)
    return md(text)
  
  rows = []
  for this_row in rows_in:
    new_row = dict(this_row)
    new_row['nicedate'] = nice_date(this_row['date'])
    new_row['html'] = format_body(this_row['body'])
    rows.append(new_row)
  return rows

def fetch_single_note(id):
  rows = dbq('SELECT * FROM notes WHERE id LIKE ?', (id,))
  if len(rows) > 0: 
    return parse_notes(rows)[0]
  else:
    return None

def fetch_single_source(id):
  rows = dbq('SELECT * FROM notes WHERE id LIKE ?', (id,))
  if len(rows) > 0: 
    return parse_notes(rows)[0]
  else:
    return None

# Search ops -------------------------------------------------------------------
def fetch_notes_by_criteria(keywords = [], search_text = '',
                            limit = 30, offset = 0):
  """Returns note summary via keyword intersection and search. If either is None,
  they are ignored. If both are None all notes are returned
  
  Important SQL snippets:
  -> This allows us to select keywords as a comma separated list
  SELECT notes.*, group_concat(keywords.name) AS kwds FROM notes 
    INNER JOIN keywords_notes ON keywords_notes.note_id = notes.id 
    INNER JOIN keywords on keywords_notes.keyword_id = keywords.id 
    WHERE notes.id IN (.....) GROUP BY notes.id;
  
  -> This allows us to do keyword intersection
  SELECT notes.* FROM notes WHERE id IN
    (SELECT kn.note_id FROM keywords_notes AS kn 
    WHERE kn.keyword_id IN 
    (SELECT k.id FROM keywords k WHERE %s) <-put in the keyword clause here
    GROUP BY kn.note_id HAVING COUNT(*) = %d)
    
  --> The combined SQL is
  SELECT notes.*, group_concat(keywords.name) AS kwds FROM notes 
    INNER JOIN keywords_notes ON keywords_notes.note_id = notes.id 
    INNER JOIN keywords on keywords_notes.keyword_id = keywords.id 
    WHERE notes.id IN 
      (SELECT kn.note_id FROM keywords_notes AS kn 
       WHERE kn.keyword_id IN 
      (SELECT k.id FROM keywords k WHERE %s) <-put in the keyword clause here
       GROUP BY kn.note_id HAVING COUNT(*) = %d) 
    GROUP BY notes.id;
    
    
  """
  #This allows us to select keywords as a comma separated list
  query = 'SELECT * FROM notes '
  arg_list = []
  search_text = search_text.strip()
  if search_text != '':
    query += ' WHERE (notes.title LIKE ? OR notes.body LIKE ?)'
    arg_list += ["%%%s%%" %search_text]
    arg_list += ["%%%s%%" %search_text]
     
  if len(keywords) > 0:
    if search_text != '':
      query += ' AND '
    else:
      query += ' WHERE '
    key_query = ' k.name=? '
    arg_list += [keywords[0]]
    for n in range(1,len(keywords)):
      key_query += ' OR k.name=? '
      arg_list += [keywords[n]]
    query += \
    """ notes.id IN
    (SELECT kn.note_id FROM keywords_notes AS kn 
    WHERE kn.keyword_id IN 
    (SELECT k.id FROM keywords k WHERE %s) 
    GROUP BY kn.note_id HAVING COUNT(*) = %d)""" %(key_query,len(keywords))
  query += ' GROUP BY notes.id ORDER BY date DESC LIMIT ? OFFSET ?'
  arg_list += [limit,offset]
  return parse_notes(dbq(query, arg_list))

def populate_new_source_from_pubmed_query(query):
  """Given a query fetch the first matching citation from pubmed."""
  source = get_empty_source()
  if query != '':
    xml = pubmed.citation_from_query(query)
    if xml != None:
      source = pubmed.parse_pubmed_xml_to_source(xml, source = source)
    else:
      source['title'] = query
  return source

def generate_citekey(source):
  """Generates a non duplicate citekey using first author last name and year"""
  au_text = source['author']
  last_name = ''
  if au_text != '':
    au_line = au_text.split("\n")
    if au_line[0] != '':
      name_frags = au_line[0].split(',')
      if name_frags[0] != '':
        last_name = name_frags[0]

  citekey = 'source' + source['id']
  if last_name != '':
    base = last_name.lower() + source['year']
    succ = 1
    citekey = base
    id = source['id']
    query = "SELECT COUNT(*) FROM sources WHERE citekey=? AND id <> ?"
    row = dbq(query, (citekey,id))
    while row[0]['COUNT(*)'] != 0:
      citekey = base + '(%d)' %succ
      succ += 1
      print citekey,row[0].keys()
      row = dbq(query, (citekey,id))
      
  return citekey

def create_new_source(source):
  source['citekey'] = generate_citekey(source)
  fields = get_source_fields()
  query = 'INSERT INTO sources ('
  query += fields[1] #ignore id
  for n in range(2,len(fields)):
    query += ', ' + fields[n]
  query += ') VALUES (?'
  for n in range(2,len(fields)):
    query += ',?'
  query += ')'
  bindings = []
  for n in range(1,len(fields)):
    bindings.append(source[fields[n]])
  source['id'] = dbq(query, bindings)
  return source

def save_source(source):
  if source['citekey'] == '':
    source['citekey'] = generate_citekey(source)
  fields = get_source_fields()
  query = 'UPDATE sources SET '
  query += fields[1] + '=?'
  for n in range(2,len(fields)):
    query += ',' + fields[n] + '=?'
  query += ' WHERE id LIKE ?'
  bindings = []
  for n in range(1,len(fields)):
    bindings.append(source[fields[n]])
  bindings.append(source['id'])
  dbq(query, bindings)

# Common use pages -------------------------------------------------------------
  
@route('/')  
def index_page():
  """Main page served by chotha. If called by itself it pulls out all the notes
  and papers in reverse time order, showing the  ."""
  search_text = request.GET.get('search_text', '')
  cskeyword_list = request.GET.get('cskeyword_list', '')
  page = int(request.GET.get('page', 0))
  perpage = int(request.GET.get('perpage', 30))
  offset = page * perpage
  limit = perpage
  current_keywords = cskeystring_to_list(cskeyword_list)
  rows = fetch_notes_by_criteria(keywords = current_keywords, 
                                 search_text = search_text, limit=limit, offset=offset)
  candidate_keywords = fetch_conjunction_candidates(current_keywords)
  title = ''
  if search_text != '':
    title += '"' + search_text + '"'
  if cskeyword_list != '':
    if search_text != '':
      title += '+'
    title += cskeyword_list
  output = template('index', rows=rows, candidate_keywords=candidate_keywords, 
                    cskeyword_list = cskeyword_list,
                    search_text = search_text,
                    page = page,
                    perpage = perpage,
                    title = title,
                    view='list')
  return output

@route('/note/:id')
def show_note_page(id):
  note = fetch_single_note(id)
  title = note['title']
  output = template('index', note=note, 
                    title=title,
                    view='note')
  return output

@route('/source/:id')
def show_source_page(id):

  source = dbq('SELECT * FROM sources WHERE id LIKE ?', (id,))[0]
  output = template('index', source=source,
                    title='%s' %source['citekey'], view='source')
  return output

#We use POST for creating/editing the entries because these operations have 
#lasting observable effects on the state of the world
#
@route('/new', method='POST')
def create_note_action():

  title = unicode(request.POST.get('title', '').strip(),'utf_8')
  body = unicode(request.POST.get('body', '').strip(),'utf_8')
  key_list = unicode(request.POST.get('key_list', '').strip(),'utf_8')
  ispaper = request.POST.get('ispaper', 'no')
  note = {'title': title, 'body': body, 'key_list': key_list}
  if ispaper=='yes':
    #Now, we should create the sidecar citation object and open for editing
    #The title is interpreted as a search string, and the first hit is 
    #returned. It is best to enter the doi or pmid
    #If blank populate will just present us with a blank source forms for us 
    #to fill out
    query = title
    source = populate_new_source_from_pubmed_query(query)
    source = create_new_source(source)#Now we have the id
    note['source_id'] = source['id']
    
  note = create_new_note(note)

  if ispaper=='yes':
    #We get a chance to see and edit the citation component
    return edit_source(id=source['id'])
  else:
    return index_page()

@route('/edit/:id')
def edit_note(id=None):
  
  note = fetch_single_note(id)
  output = template('index', note=note, 
                    title='Editing %s' %note['title'], view='edit')
  return output

@route('/editsource/:id')
def edit_source(id=None):
  
  source = dbq('SELECT * FROM sources WHERE id LIKE ?', (id,))[0]
  output = template('index', source=source,
                    title='Editing %s' %source['citekey'], view='editsource')
  return output
  
@route('/save/:id', method='POST')
def save_note_action(id=None):

  date = request.POST.get('date', '').strip()
  title = unicode(request.POST.get('title', '').strip(),'utf_8')
  body = unicode(request.POST.get('body', '').strip(),'utf_8')
  key_list = unicode(request.POST.get('key_list', '').strip(),'utf_8')  
  note = {'id': int(id), 'date': date, 'title': title, 'body': body, 'key_list': key_list}
  save_note(note)
  output = template('index', note=note,
                    title='Saved %s' %note['title'], view='note')  
  return output

@route('/savesource/:id', method='POST')
def save_source_action(id):
  fields = get_source_fields()
  source = get_empty_source()
  for f in fields:
    val = request.POST.get(f, None)
    if val != None:
      source[f] = unicode(val.strip(),'utf_8')
  save_source(source)
  output = template('index', source=source,
                    title='Saved %s' %source['citekey'], view='source')  
  return output

# Configuration helpers --------------------------------------------------------
def create_default_config_file():
  config.add_section('Basic')
  config.set('Basic', 'dbname', 'rriki_example.sqlite3')
  config.set('Basic', 'host', 'localhost')
  config.set('Basic', 'port', '3020')
  
  config.add_section('Advanced')  
  config.set('Advanced', 'debug', 'True')
  config.set('Advanced', 'reloader', 'True')
  
  with open('chotha.cfg', 'wb') as configfile:
    config.write(configfile)  

def load_config():
  result = config.read('chotha.cfg')
  if len(result) == 0:
    create_default_config_file()

def save_config():
  with open('chotha.cfg', 'wb') as configfile:
    config.write(configfile)  
  

# Configuration pages ---------------------------------------------------------  
@route('/selectdb/:newdbname')
def select_database(newdbname='pylogdb.sqlite3'):
  globals()['dbname']=newdbname
  config.set('Basic', 'dbname', newdbname)
  save_config()
  return index_page()

@route('/createdb/:newdbname')
def new_database(newdbname='pylogdb.sqlite3'):
  globals()['dbname']=newdbname
  create_database()
  config.set('Basic', 'dbname', newdbname)
  save_config()
  return index()

# Nasty stuff -------------------------------------------------------------------
@bottle.route('/lib/:filename#.*#')
def static_file(filename):
    bottle.send_file(filename, root='./lib')


# For testing only -------------------------------------------------------------
@route('/createtestdb/:newdbname')
def new_testing_database(newdbname='chotha_test.sqlite3'):
  globals()['dbname']=newdbname
  create_database()
  #populate_database_with_test_data()
  config.set('Basic', 'dbname', newdbname)
  save_config()
  return index_page()

def populate_database_with_test_data():
  """Populate the tables with some deterministic data"""  
  query = """INSERT INTO notes (title,date) VALUES ('Michaela','2010-12-31');
  INSERT INTO sources (title,citekey) VALUES ('A paper','crusty1956');  
  INSERT INTO notes (title,date,source_id) VALUES ('A paper','2010-12-31',1);"""
  dbq(query)
  
  
if __name__ == "__main__":
  
  load_config()
  deb = config.getboolean('Advanced', 'debug')
  host = config.get('Basic','host')
  port = config.getint('Basic', 'port')
  relo = config.getboolean('Advanced', 'reloader')
  globals()['dbname'] = config.get('Basic','dbname')
  debug(deb)
  bottle.run(host=host, port=port,reloader=relo)
  #bottle.run(host='localhost', port=8080)
