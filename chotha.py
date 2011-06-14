import datetime, sqlite3, markdown2 as markdown
md = markdown.markdown
import bottle
from bottle import route, debug, template, request, validate, send_file, error

#For the wiki links substitution. I global it thinking to save computation
import re
pnote = re.compile(r'\[(.+?)\]\[note:(\d+?)\]')

import ConfigParser
config = ConfigParser.RawConfigParser()
dbname = None

import pubmed

import logging
logger = logging.getLogger('chotha')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
logger.addHandler(ch)

#Always start with id
source_fields = [
['id ','INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL'],
['abstract', 'TEXT'],
['address','VARCHAR(255)'],
['author','VARCHAR(255)'],
['booktitle','VARCHAR(255)'],
['body', 'TEXT'],
['chapter','VARCHAR(255)'],
['citekey','VARCHAR(255)'],
['created_at','DATETIME'],
['doi','VARCHAR(255)'],
['edition','VARCHAR(255)'],
['editor','VARCHAR(255)'],
['filing_index','VARCHAR(255)'],
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
['year','INTEGER'],
]

def get_cursor():
  """Returns us a cursor and connection object to our database."""
  conn = sqlite3.connect(dbname)
  conn.row_factory = sqlite3.Row
  c = conn.cursor()
  return c, conn

def create_database():
  """Creates a new empty database.
  source_fields list."""
  c, conn = get_cursor()
  c.execute('CREATE TABLE "notes" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "title" VARCHAR(255), "date" DATETIME, "body" TEXT)')
  #c.execute('CREATE TABLE "sources" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "abstract" text, "address" varchar(255), "author" varchar(255), "booktitle" varchar(255), "chapter" varchar(255), "citekey" varchar(255), "edition" varchar(255), "editor" varchar(255), "filing_index" varchar(255), "howpublished" varchar(255), "institution" varchar(255), "journal" varchar(255), "month" varchar(255), "number" varchar(255), "organization" varchar(255), "pages" varchar(255), "publisher" varchar(255), "school" varchar(255), "series" varchar(255), "title" varchar(255), "source_type" varchar(255), "url" varchar(255), "volume" varchar(255), "year" integer, "body" text)')
  query = 'CREATE TABLE "sources" ('
  query += '"%s" %s' %(source_field[0][0], source_field[0][1]) 
  for n in range(1,len(source_field)):
    query += ', "%s" %s' %(source_field[n][0], source_field[n][1])
  query += ')'
  c.execute(query)
  c.execute('CREATE TABLE "keywords" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "name" VARCHAR(255))')  
  c.execute('CREATE TABLE "keywords_notes" ("keyword_id" INTEGER, "note_id" INTEGER, PRIMARY KEY (keyword_id, note_id))')
  c.execute('CREATE TABLE "keywords_sources" ("keyword_id" INTEGER, "source_id" INTEGER, PRIMARY KEY (keyword_id, source_id))')
  conn.commit()

def find_or_create_keyword(word, c):
  """Find or create a keyword and return the keyword id. c is a cursor"""
  c.execute('SELECT id FROM keywords WHERE word LIKE ?', (word))
  row = c.fetchone()
  if len(row) == 0:
    c.execute('INSERT INTO keywords (word) VALUES (?)', (word))
    id = c.lastrowid
  else:
    id = row['id']
  return id
  
def save_note_keywords(note, c):
  """Keywords are a comma separated list, we first extract that."""
  keywords = note['keywords'].split(',')
  note_id = note['id']
  for keyword in keywords:
    keyword_id = find_or_create_keyword(keyword.strip(), c)
    c.execute('INSERT OR REPLACE INTO keywords_notes (keyword_id,note_id) values (?,?)', (keyword_id,note_id))

def create_new_note(note):
  c, conn = get_cursor()
  now = datetime.datetime.now()
  c.execute("INSERT INTO notes (title,date,body) VALUES (?,?,?)", 
            (note['title'], now, note['body']))
  note['id'] = c.lastrowid #Now needed for the keyword saves
  save_note_keywords(note, c)
  conn.commit()

def save_note(note):
  """We then refetch the saved note so we can display it."""
  c, conn = get_cursor()
  c.execute("UPDATE notes SET date = ?, title = ?, body = ? WHERE id LIKE ?", 
            (note['date'], note['title'], note['body'], note['id']))
  save_note_keywords(note, c)
  conn.commit()
  return fetch_single_note(note['id'])[0]

def parse_notes(rows_in):
  """Given a list of row objects returned by a fetch, copy the data into a new
  dictionary after running each entry through the markdown parser."""
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
    new_row = {
      'id': this_row['id'],
      'date': this_row['date'],
      'nicedate': nice_date(this_row['date']),
      'title': this_row['title'],
      'body': format_body(this_row['body']),
      'markup text': this_row['body']}
    rows.append(new_row)
  return rows

def fetch_single_note(id):
  c, conn = get_cursor()
  c.execute('SELECT * FROM notes WHERE id LIKE ?', (id,))
  return parse_notes(c.fetchall())

def save_note(note):
  """We then refetch the saved note so we can display it."""
  c, conn = get_cursor()
  c.execute("UPDATE notes SET date = ?, title = ?, body = ? WHERE id LIKE ?", 
            (note['date'], note['title'], note['body'], note['id']))
  conn.commit()
  return fetch_single_note(note['id'])[0]

def fetch_conjunction_candidates(keywords = None):
  """Given the keyword, fetch a list of keywords that appear in conjunction
  with it in the database.
  
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
  if keywords != None:
    kq = ' k.name=? ' 
    for n in range(1,len(keywords)):
      kq += ' OR k.name=? ' 
    
    query = \
    'SELECT k.name FROM keywords k WHERE k.id IN \
      (SELECT DISTINCT kn.keyword_id FROM keywords k, keywords_notes kn WHERE kn.note_id IN \
        (SELECT kn.note_id FROM keywords_notes AS kn WHERE kn.keyword_id IN \
         (SELECT k.id FROM keywords k WHERE %s) \
         GROUP BY kn.note_id HAVING COUNT(*) = ?) \
       UNION \
       SELECT DISTINCT ks.keyword_id FROM keywords k, keywords_sources ks WHERE ks.source_id IN \
        (SELECT ks.source_id FROM keywords_sources AS ks WHERE ks.keyword_id IN \
         (SELECT k.id FROM keywords k WHERE %s) \
         GROUP BY ks.source_id HAVING COUNT(*) = ?)) \
     AND k.id NOT IN (SELECT k.id FROM keywords k WHERE %s)' %(kq,kq,kq)
    arg_list = keywords + [len(keywords)] + keywords + [len(keywords)] + keywords
  else:
    query = 'SELECT k.name FROM keywords k'
  logger.debug(query)
  c, conn = get_cursor()
  c.execute(query, arg_list)
  return c.fetchall()

  

def fetch_notes_by_criteria(keywords = None, search_text = None,
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
  c, conn = get_cursor()
  #This allows us to select keywords as a comma separated list
  query = 'SELECT notes.*, group_concat(keywords.name) AS kwds FROM notes \
    INNER JOIN keywords_notes ON keywords_notes.note_id = notes.id \
    INNER JOIN keywords on keywords_notes.keyword_id = keywords.id'
  arg_list = []
  if search_text != None:
    search_text = search_text.strip()
    query += ' WHERE (notes.title LIKE ? OR notes.body LIKE ?)'
    arg_list += ["%%%s%%" %search_text]
    arg_list += ["%%%s%%" %search_text]
     
  if keywords != None:
    if search_text != None:
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
  
  query += ' GROUP BY notes.id ORDER BY date DESC LIMIT %d OFFSET %d' %(limit, offset)
  logger.debug(query)
  logger.debug(arg_list)
  c.execute(query, arg_list)
  return parse_notes(c.fetchall())

def populate_new_source_from_pubmed_query(query):
  """Given a query fetch the first matching citation from pubmed."""
  source = {}#Create the fields pubmed does not return
  xml = pubmed.citation_from_query(query)
  return pubmed.parse_pubmed_xml_to_source(xml, source = {})

def create_new_source(source):
  query = 'INSERT INTO sources ('
  query += source_field[1][0]
  for n in range(2,len(source_field)):
    query += ', ' + source_field[n][0]
  query += ') VALUES (?'
  for n in range(2,len(source_field)):
    query += ',?'
  query += ')'
  value_list = []
  for n in range(1,len(source_field)):
    value_list.append(source.get(source_field[n]),'')
  
  c, conn = get_cursor()
  c.execute(query, value_list)
  conn.commit()
  return fetch_single_source()

def save_source(source):
  query = 'UPDATE sources SET '
  query += source_field[1][0] + '=?'
  for n in range(2,len(source_field)):
    query += ',' + source_field[n][0] + '=?'
  query += ' WHERE id LIKE ?'
  value_list = []
  for n in range(1,len(source_field)):
    value_list.append(source.get(source_field[n]),'')
  value_list.append(source['id'])
  
  c, conn = get_cursor()
  c.execute(query, value_list)
  conn.commit()
  return fetch_single_source()

def populate_database_with_test_data():
  """Populate the tables with some deterministic data"""

  note = {'title': 'Rabbits', 'body': 'Rabbits are lagomorphs with big ears'}
  create_new_note(note)
  note = {'title': 'Cats', 'body': 'Cats are cuddly felines with pointy ears'}
  create_new_note(note)
  note = {'title': 'Pandas', 'body': 'Pandas are just cute'}
  create_new_note(note)  

def get_year_count_list():
  """Return a list of years that are in our database and the number of entries
  in that year."""
  c, conn = get_cursor()
  c.execute("select strftime('%Y',date) as year, count(date) as cnt from entries group by year order by year desc")
  rows = c.fetchall()
  return rows

# Common use pages -------------------------------------------------------------
  
@route('/')  
def v_index():
  """Main page serve function. 
  If edit is True and id has a integer value,
  instead of showing a form for a new entry at the top, setup a form for
  editing the entry with id. Scroll to that form using an anchor (all this magic
  happens in the template)
  If edit is False but id is an integer, scroll to that entry using an anchor.
  This is used to show us an entry we have just edited."""
  
  search_text = request.GET.get('search_text', None)
  cskeyword_list = request.GET.get('cskeyword_list', None)
  if cskeyword_list != None:
    current_keywords = cskeyword_list.split(',')
    for keyword in current_keywords:
      keyword = keyword.strip()
  else:
    current_keywords = None
  
  rows = []
  candidate_keywords = []
  #rows = fetch_notes_by_criteria(keywords = current_keywords, search_text = search_text, limit=100)
  candidate_keywords = fetch_conjunction_candidates(current_keywords)
  output = template('index', rows=rows, candidate_keywords=candidate_keywords, view='list')
  return output

@route('/note/:id')
def v_show_note(id):
  rows = fetch_single_note(id)
  output = template('index', rows=rows, view='single')
  return output

#We use POST for creating/editing the entries because these operations have 
#lasting observable effects on the state of the world
#
@route('/new', method='POST')
def v_new_note():

  title = unicode(request.POST.get('title', '').strip(),'utf_8')
  body = unicode(request.POST.get('body', '').strip(),'utf_8')
  note = {'title': title, 'body': body}
  create_new_note(note)  
  return index()

@route('/edit/:id')
def v_edit_note(id=None):
  
  note = fetch_single_note(id)[0]
  output = template('index', note=note, 
                    title='Editing', view='edit')
  return output

@route('/save/:id', method='POST')
def v_save_note(id=None):

  date = request.POST.get('date', '').strip()
  title = unicode(request.POST.get('title', '').strip(),'utf_8')
  body = unicode(request.POST.get('body', '').strip(),'utf_8')
  note = {'id': int(id), 'date': date, 'title': title, 'body': body}
  note = save_note(note)
  output = template('index', note=note,
                    title='Saved', view='saved')  
  return output

@route('/search')
def search(text=''):
  """."""
  text = unicode(request.GET.get('searchtext', '').strip(),'utf_8')
  rows = fetch_entries_by_search(text)
  output = template('index', rows=rows, 
                    year=str(datetime.date.today().year), year_count=get_year_count_list(),
                    title='Searched for "%s". Found %d entries' %(text,len(rows)), view='searchlist')
  return output


@route('/quit')
def quit_server():
  """A bit extreme, but really the only thing that worked, including exit(0),
  and SIGINT. Not needed if we use it from the command line or as a startup
  server, but essential when we use it as an app."""
  bottle.os._exit(0)  

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
  return index()

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
@route('/testme')
def test_me():
  search_text = request.GET.get('search_text', None)
  cskeyword_list = request.GET.get('cskeyword_list', None)
  return search_text, cskeyword_list
  

@route('/createtestdb/:newdbname')
def new_testing_database(newdbname='chotha_test.sqlite3'):
  globals()['dbname']=newdbname
  create_database()
  populate_database_with_test_data()
  config.set('Basic', 'dbname', newdbname)
  save_config()
  return index()
  
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
