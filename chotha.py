import datetime, apsw, markdown, bottle, re, logging, pubmed, ConfigParser, citationmanager as cm
from bottle import route, debug, template, request

#Config file
config = ConfigParser.RawConfigParser()

#database name
dbname = None

#set up logging
logger = logging.getLogger('chotha')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)

# Database operations ---------------------------------------------------------
def dbq(query, bindings=None, many=False, conn=None):
  """Utility function to handle db queries. Based on query type, the function
  returns last rowid or rows (which is a list of dictionaries)"""
  if not bindings: bindings = []

  #Get the first word of the query to figure out what we should return
  cmd = query.split(' ',1)[0].upper()
  
  if conn is None:
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
  ['doi','VARCHAR(255)'],
  ['edition','VARCHAR(255)'],
  ['editor','VARCHAR(255)'],
  ['howpublished','VARCHAR(255)'],
  ['institution','VARCHAR(255)'],
  ['journal','VARCHAR(255)'],
  ['month','VARCHAR(255)'],
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
  dbq('CREATE TABLE "wordcloud" ("word" TEXT PRIMARY KEY, "count" INTEGER)')

#Keyword ops -------------------------------------------------------------------
def cskeystring_to_list(cskeystring):
  """Converts a comma separated list of keywords (which is how we store them
  in the keywords field in a note) to a list of keywords."""
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
    if not len(row):
      id = dbq('INSERT INTO keywords (name) VALUES (?)', (name,))
    else:
      id = row[0]['id']
    kids.append(id)
  return kids

def save_note_keywords(note):
  """Extract list of keywords from keywords field in notes. Find or create
  keywords in db. Associate keywords with note in link table. Delete keywords no longer present in link table. This last operation becomes very
  expensive if we have a large number of keywords"""
  note_id = note['id']    
  dbq('DELETE FROM keywords_notes WHERE note_id=?', (note_id,))#Delete original list
  keywords = cskeystring_to_list(note['key_list'])  #Create new list
  new_kids = find_or_create_keywords(keywords)
  if len(new_kids) > 0:
    bindings = []
    for kid in new_kids:
      bindings.append([kid, note_id])
    dbq('INSERT INTO keywords_notes (keyword_id,note_id) VALUES (?,?)', 
        bindings, many=True)
  dbq('DELETE FROM keywords WHERE id NOT IN (SELECT keyword_id FROM keywords_notes)')  #Clean up unused keywords
  

#TODO fix to remove references to sources
def fetch_conjunction_candidates(keywords=None):
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
  if not keywords: keywords = []
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

def update_word_cloud(oldtext, newtext):
  """Pass in a list of notes. This will either create new entries or increment
  existing ones by 1 depending on whether the entry exists."""
  import wordcloud
  wordcloud.update_word_cloud(oldtext, newtext, dbname)

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
  update_word_cloud('', note['body'])
  return note

def save_note(note):
  """We fetch the old note before saving the new note so we can update the
  wordcloud."""
  old_note = fetch_single_note(note['id'])
  dbq("UPDATE notes SET date = ?, title = ?, body = ?, key_list = ? WHERE id LIKE ?", 
      (note['date'], note['title'], note['body'], note['key_list'], note['id']))
  save_note_keywords(note)
  update_word_cloud(old_note['body'], note['body'])

#TODO handle flag for sources
def format_notes(rows_in, taglist=False):
  """Formats notes by converting markdown, creating source and note links and
  making a nice format for the dates.

  Given a list of row objects returned by a fetch, copy the data into a new
  dictionary after running each entry through the markdown parser.

  If taglist is true then we organize sources in the note by tag. This is a
  potentially time-consuming operation and we only do this when we are showing
  a single note.
  """

  md = markdown.Markdown(extensions=['chothamathml']).convert
  pnote = re.compile(r'\[(.+?)\]\[note:(\d+?)\]')#For the wiki links substitution.
  psourceold = re.compile(r'\[source:(.+?)\]')#For the wiki links substitution.
  psource = re.compile(r'\[:(.+?)\]')#shortened source link code
  ptags = re.compile(r'\[t:(.+?)\]')#Used to remove tags from the text

  def nice_date(date):
    nd = datetime.date(int(date[0:4]),int(date[5:7]),int(date[8:10]))
    return nd.strftime('%a %b %d, %Y')
  
  def format_body(body, taglist=False):
    def tagged_bibliography(text):
      """Go through text, extract sources with tags, build a list of tags
      and associated sources, make a section of the document repeated lists
      of the papers (formatted in markdown)."""

      tag_list = {}
      pst = re.compile(r'\[:(.+?)\]\[t:(.+?)\]')
      ts_list = pst.findall(text)
      for ts in ts_list:
        this_citekey = ts[0]
        for tt in ts[1].split(','):
          this_tag = tt.strip()
          if this_tag is '':
            continue

          if this_tag not in tag_list.keys():
            tag_list[this_tag] = [this_citekey]
          else:
            tag_list[this_tag].append(this_citekey)

      if len(tag_list) == 0:
        return text

      #new_text = u'Tags: '
      new_text = u''
      tags = sorted(tag_list.keys(), key=lambda w: w.lower())
      #for n,t in enumerate(tags):
      #  if n > 0: new_text += ', '
      #  new_text += u'[{:s}](#{:d})'.format(t,n)

      new_text += '\n'
      for n,t in enumerate(tags):
        new_text += u'{:s}<a id="{:d}">: '.format(t,n)
        for idx,src in enumerate(sorted(tag_list[t])):
          if idx > 0: new_text += ', '
          new_text += u'[:{:s}]'.format(src)
        new_text += '\n\n'
      new_text += '\n ---- \n\n'
      return new_text + text


    def nlinx(match):
      return '<a href="/note/%s">%s</a>' %(match.group(2),match.group(1))

    def slinx(match):
      return '<a href="/sourcecitekey/%s">%s</a>' %(match.group(1),match.group(1))

    if taglist:
      text = tagged_bibliography(body)
      text = ptags.sub('', text)#Remove tags so they are not visible
    else:
      text = ptags.sub('', body)#Remove tags so they are not visible
    text = pnote.sub(nlinx, text)
    text = psource.sub(slinx, text)
    text = psourceold.sub(slinx, text)
    
    return md(text)
  
  rows = []
  for this_row in rows_in:
    new_row = dict(this_row)
    new_row['nicedate'] = nice_date(this_row['date'])
    new_row['html'] = format_body(this_row['body'], taglist)
    rows.append(new_row)
  return rows

def extract_sources_from_note(note):
  """Does the magic for source export. Finds all source links in the note,
  retrieves them from the database. Tells us which ones are not found."""
  def sources_not_found(req_scks, rows):
    fnd_scks = [row['citekey'] for row in rows]
    miss_scks = set(req_scks) - set(fnd_scks)
    return miss_scks
    
  psource = re.compile(r'\[source:(.+?)\]')
  psource2 = re.compile(r'\[:(.+?)\]')
  scks = psource.findall(note['body'])
  scks2 = psource2.findall(note['body'])
  scks += scks2
  scks_string = ', '.join('?' for dummy in scks)
  rows = dbq('SELECT * FROM sources WHERE citekey IN (%s) ORDER BY citekey' %scks_string, scks)
  miss_scks = sources_not_found(scks, rows)
  return rows, miss_scks

def fetch_single_note(id):
  """Grab single note from database given its id."""
  rows = dbq('SELECT * FROM notes WHERE id LIKE ?', (id,))
  if len(rows) > 0: 
    return format_notes(rows, True)[0]#We want the tags analyzed
  else:
    return None

def fetch_single_source(id):
  """Grab source data and its linked note id given source id."""
  rows = dbq('SELECT sources.*,notes.id AS nid FROM sources,notes WHERE sources.id LIKE ? AND notes.source_id = sources.id', (id,))
  if len(rows) > 0:
    #Preprocess to fill out bibtex, because it is useful
    return rows[0]
  else:
    return None

def fetch_single_source_by_citekey(citekey):
  """Grab source data and its linked note id given source citekey. This is used
  when we click a source link in a note or collate sources in a note for export"""
  rows = dbq('SELECT sources.*,notes.id AS nid FROM sources,notes WHERE sources.citekey LIKE ? AND notes.source_id = sources.id', (unicode(citekey,'utf-8'),))
  if len(rows) > 0:
    return rows[0]
  else:
    return None

# Search ops -------------------------------------------------------------------
def fetch_notes_by_criteria(keywords=None, search_text='', limit=10, offset=0):
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
  if not keywords: keywords = []
  query = 'SELECT id FROM notes '
  arg_list = []
  
  if search_text.startswith(':s '):
    """This lets us perform arbitrary SQL queries on our db for sources.
    Activate it by typing ":s <where clause>" in the search box. The
    where clause should omit the WHERE keyword. This is designed as a desktop
    app used by the owner, so we trust him not to sabotage himself by doing
    strange things."""
    where_clause = search_text[2:]
    query = "SELECT id FROM notes WHERE source_id IN (SELECT id FROM sources WHERE %s)" %where_clause
  else:
    #Do a regular search
    if search_text != '':
      query += ' WHERE (notes.title LIKE ? OR notes.body LIKE ?) '
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
    query += ' GROUP BY notes.id'

  query += ' ORDER BY notes.date DESC'

  rows = dbq(query, arg_list)
  lrows = len(rows)
  
  query_id_list = ''
  n = offset
  while lrows > n < offset+limit:
    query_id_list += str(rows[n]['id']) + ','
    n += 1
  query_id_list = query_id_list.rstrip(',')
  query = 'SELECT * FROM notes WHERE id IN (' + query_id_list + ') ORDER BY date DESC'
  return format_notes(dbq(query)), lrows

def populate_new_source_from_pubmed_query(query):
  """Given a query fetch the first matching citation from pubmed."""
  source = get_empty_source()
  if query != '':
    xml = pubmed.citation_from_query(query)
    if xml is not None:
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
        last_name = last_name.replace("'","_") #Apostrophe is an illegal citekey character.

  citekey = 'source' + source['id'] #cite key for sources with no authors
  if last_name != '':
    base = last_name.lower() + source['year']
    succ = 1
    citekey = base
    id = source['id']
    query = "SELECT COUNT(*) FROM sources WHERE citekey=? AND id <> ?"
    row = dbq(query, (citekey,id))
    while row[0]['COUNT(*)']:
      citekey = base + '_%d' %succ
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

# Utility functions ------------------------------------------------------------
def wtemplate(tmplt,**kwargs):
  """Needed a wrapper to the template call to include common options etc."""
  #Some defaults to make life easier
  defaults = {
  'total_found': 1, 
  'cskeyword_list': '',
  'candidate_keywords': [],
  'search_text': '',
  'limit': 10,
  'offset': 0,
  'title': 'Chotha',
  'rows': [None] #Dummy, causes display to say one thing is found
  }
  for key in defaults.keys():
    if not kwargs.has_key(key):
      kwargs[key] = defaults[key]   
  kwargs['desktop_cskeyword_list'] = config.get('User','desktop')
  return template(tmplt,**kwargs)

# Common use pages -------------------------------------------------------------

@route('/')  
def index_page():
  """Main page served by chotha. If called by itself it pulls out all the notes
  and papers in reverse time order, showing the  ."""
  search_text = request.GET.get('search_text', '')
  cskeyword_list = request.GET.get('cskeyword_list', '')
  offset = int(request.GET.get('offset',0))
  limit = int(request.GET.get('limit',10))

  current_keywords = cskeystring_to_list(cskeyword_list)
  rows, Nrows = fetch_notes_by_criteria(keywords = current_keywords, 
                                 search_text = search_text, 
                                 offset=offset, limit=limit)
  #Nrows is the total number of results
  candidate_keywords = fetch_conjunction_candidates(current_keywords)
  
  title = ''
  if search_text != '':
    title += '"' + search_text + '"'
  if cskeyword_list != '':
    if search_text != '':
      title += '+'
    title += cskeyword_list
  if title == '':
    title = 'Home'
  output = wtemplate('index', rows=rows, candidate_keywords=candidate_keywords,
                    total_found = Nrows, 
                    cskeyword_list = cskeyword_list,
                    search_text = search_text,
                    limit = limit,
                    offset = offset,
                    title = title,
                    view='list')
  return output

@route('/new')
def new_page():
  """Returns page with slot for new entry."""
  cskeyword_list = request.GET.get('cskeyword_list', '')
  output = wtemplate('index', cskeyword_list = cskeyword_list,
                    title = "New entry",
                    view='new')
  return output
  
@route('/note/:id')
def show_note_page(id):
  note = fetch_single_note(id)
  title = note['title']
  output = wtemplate('index', note=note, 
                    title=title,
                    view='note')
  return output

@route('/notesourceexport/:id')
def export_sources_from_note(id):
  """We're trying out something fancy. In the note itself we set the file name
  and the mode in the first and second line."""  
  def get_filename_and_mode(note):
    lines = note['body'].splitlines()
    fname = mode = None
    for line in lines:
      if line.startswith('File:'):
        fname = line[5:].strip()
        if mode is not None:
          break
      if line.startswith('Mode:'):
        mode = line[5:].strip()
        if fname is not None:
          break
      
    if fname is None:
      fname = 'chotha.ris'
    if mode is None:
      mode = 'ris'
    
    return fname, mode
    
  note = fetch_single_note(id)
  fname, mode = get_filename_and_mode(note)
  sources, missing_citekeys = extract_sources_from_note(note)
  import citationmanager as ce
  if mode =='word':
    refcount = ce.export_MSWord_XML(fname, sources)
  elif mode =='bibtex':
    refcount = ce.export_BibTeX(fname, sources)
  elif mode =='ris':
    refcount = ce.export_RIS(fname, sources)    

  message = """<p>Wrote <b>%d</b> of <b>%d</b> valid sources present in this 
  note to <b>%s</b> as <b>%s</b>.</p>""" %(refcount, len(sources), fname, mode)
  if len(missing_citekeys) > 0:
    message += """<p>The following sources were requested but not found in the 
    database: """
    for ck in missing_citekeys:
      message += "<b>%s</b> " % ck

  output = wtemplate('index', note=note, 
                    title='Exported sources from note',
                    message = message,
                    view='note')
  
  return output

@route('/source/:id')
def show_source_page(id):
  source = fetch_single_source(id)
  output = wtemplate('index', source=source,
                    bibtex=cm.source_to_bibtex([source], include_abstract=False),
                    title='%s' %source['citekey'], 
                    view='source')
  return output

@route('/sourcecitekey/:citekey')
def show_source_page_citekey(citekey):
  source = fetch_single_source_by_citekey(citekey)
  if source is not None:
    title = '%s' %source['citekey']
    output = wtemplate('index', source=source,
                       bibtex=cm.source_to_bibtex([source], include_abstract=False),
                       title=title, view='source')

  else:
    ntitle = citekey[:-4] + ' ' + citekey[-4:]
    output = wtemplate('index',
                  title = "New entry",
                  ntitle = ntitle,  #sets up a title for the note
                  ispaper = 'CHECKED', #Checks the "this is a paper" checkbox
                  view='new',
                  message='No such source in database. Create?')
    
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
    request.GET.append('cskeyword_list',key_list)
    return index_page()

@route('/edit/:id')
def edit_note(id=None):
  note = fetch_single_note(id)
  output = wtemplate('index', note=note, 
                    title='Editing %s' %note['title'], view='edit')
  return output

@route('/editsource/:id')
def edit_source(id=None):
  source = dbq('SELECT sources.*,notes.id AS nid FROM sources,notes WHERE sources.id LIKE ? AND notes.source_id = sources.id', (id,))[0]
  output = wtemplate('index', source=source,
            source_bibtex=cm.source_to_bibtex([source]),
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
  note = fetch_single_note(note['id'])
  output = wtemplate('index', note=note,
                    title='Saved %s' %note['title'], view='note')  
  return output

@route('/savesource', method='POST')
def save_source_action():
  source = get_empty_source()
  source_bibtex = request.POST.get('bibtex', None).decode("UTF-8")
  source = cm.parse_bibtex_to_source(source_bibtex, source=source)
  source['id'] = request.POST.get('id', None)
  save_source(source)

  #source = fetch_single_source(source['id']) #We need the note id
  source['nid'] = request.POST.get('nid', None)#We need the note id
  output = wtemplate('index', source=source,
                     bibtex=cm.source_to_bibtex([source], include_abstract=False),
                    title='Saved %s' %source['citekey'], view='source')
  return output

@route('/refetchsource', method='POST')
def refetch_source_action():
  query = unicode(request.POST.get('query', '').strip(),'utf_8')
  id = request.POST.get('id','').strip()
  source = populate_new_source_from_pubmed_query(query)
  source['id'] = id #Need if before we can generate citekey
  source['citekey'] = generate_citekey(source)

  source['nid'] = request.POST.get('nid', None)#We need the note id
  output = wtemplate('index', source=source, source_bibtex=cm.source_to_bibtex([source]),
                    title='Editing %s' %source['citekey'], view='editsource')
  return output


@route('/wordcloud')
def wordcloud_page():
  wordcloud = dbq('SELECT word, count FROM wordcloud ORDER BY word ASC')
  output = wtemplate('templates/wordcloud', wordcloud=wordcloud,
                    title='wordcloud', view='wordcloud')
  return output

@route('/keyword_frequency')
def keyword_frequency_page():
  keyword_freq = dbq('SELECT k.name, count(kn.rowid),  kn.keyword_id FROM keywords as k, keywords_notes as kn WHERE k.id = kn.keyword_id GROUP BY kn.keyword_id ORDER BY count(kn.rowid) DESC')
  #keyword_freq = dbq('SELECT k.name, count(kn.rowid),  kn.keyword_id FROM keywords as k, keywords_notes as kn WHERE k.id = kn.keyword_id GROUP BY kn.keyword_id ORDER BY k.name')
  output = wtemplate('templates/keyword_frequency', keyf=keyword_freq,
    title='Keyword frequency', view='')
  return output


@route('/rebuildwordcloud')
def rebuild_wordcloud_page():
  """May take a VERY long time."""
  import wordcloud
  notes = dbq('SELECT body FROM notes')
  wordcloud.rebuild_wordcloud(notes, dbname)
  return wordcloud_page()
  

# Configuration helpers --------------------------------------------------------
def create_default_config_file():
  config.add_section('Basic')
  config.set('Basic', 'dbname', 'rriki_example.sqlite3')
  config.set('Basic', 'host', 'localhost')
  config.set('Basic', 'port', '3020')
  
  config.add_section('Advanced')  
  config.set('Advanced', 'debug', 'True')
  config.set('Advanced', 'reloader', 'True')
  
  config.add_section('User')
  config.set('User','desktop','')
  config.set('User','msword_source_fname','')
  
  with open('chotha.cfg', 'wb') as configfile:
    config.write(configfile)  

def load_config():
  result = config.read('chotha.cfg')
  if not len(result):
    create_default_config_file()

def save_config():
  with open('chotha.cfg', 'wb') as configfile:
    config.write(configfile)  
  

# Configuration pages ---------------------------------------------------------  
@route('/selectdb', method='POST')
def select_database():
  newdbname = request.POST.get('newdbname', '').strip()
  import os
  if os.path.exists(newdbname):
    logger.info('Found db %s. Switching' %newdbname)    
    globals()['dbname']=newdbname
    config.set('Basic', 'dbname', newdbname)
    save_config()
    return index_page()
  else:
    logger.info('Did not find db %s. Creating new' %newdbname)        
    return new_database()

@route('/createdb', method='POST')
def new_database():
  newdbname = request.POST.get('newdbname', '').strip()
  logger.info('Creating %s' %newdbname)  
  globals()['dbname']=newdbname
  create_database()
  config.set('Basic', 'dbname', newdbname)
  save_config()
  return index_page()

@route('/options/setdesktop/')
def set_desktop():
  """Set the current keyword conjunction list as the desktop. Passed in via GET."""
  cskeyword_list = request.GET.get('cskeyword_list', '')
  config.set('User', 'desktop', cskeyword_list)
  save_config()
  return index_page()

@route('/firsttime')
def first_time_setup():
  """Show a page with some configuration data and some simple stats."""
  dbinfo = {'note count': 0,
            'source count': 0,
            'sqlite version': apsw.sqlitelibversion()}
  from sys import version
  dbinfo['python version'] = version

  cfg = {'dbinfo': dbinfo,
         'cfg file': config}
  return template('templates/config', cfg=cfg)

@route('/config')
def show_config_page():
  """Show a page with some configuration data and some simple stats."""
  dbinfo = {
    'note count': dbq("SELECT COUNT(id) FROM NOTES WHERE source_id IS NULL")[0][
                  "COUNT(id)"], 'source count':
      dbq("SELECT COUNT(id) FROM NOTES WHERE source_id IS NOT NULL")[0][
      "COUNT(id)"], 'sqlite version': apsw.sqlitelibversion()}
  from sys import version
  dbinfo['python version'] = version
  
  cfg = {'dbinfo': dbinfo,
         'cfg file': config}
  return template('templates/config', cfg=cfg)
  
# File stuff -------------------------------------------------------------------
@bottle.route('/static/:filename#.*#')
def static_file(filename):
  return bottle.static_file(filename, root='./static')


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
