"""Convert rriki database to chotha database.

Conversion of RRiki database to Chotha:
--------------------------------------
* Create a new chotha database
* Copy over all the notes as is, dropping the created_at and updated_at columns
* Copy over all the sources as is, dropping the created_at, updated_at and url columns
* For each source, create a new note and fill in the source_id appropriately
set the note date as the source created_at date and the note title as the paper
title + citekey
=> note and source ids remain the same, but now we have a bunch of extra notes at the end
* For each note, grab the keywords
   * For each keyword, use the path to separate out the keywords into components words.
   *  Keywords with commas - each part is a separate keyword.
   * Associate each keyword with note
* For each source, grab the keywords
   * For each keyword, use the path to separate out the keywords into components words.
   *  Keywords with commas - each part is a separate keyword.
   * Find the note that goes with the source (source ids are conserved) and associate the keywords with that note
   
"""
import os, sys, apsw

def dbq(query, bindings = [], many = False, conn = None):
  """Utility function to handle db queries. Based on query type, the function
  returns last rowid or rows (which is a list of dictionaries)"""

  #Get the first word of the query to figure out what we should return
  cmd = query.split(' ',1)[0].upper()
  
#  if conn == None:
#    conn = apsw.Connection(dbname)
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


# Create a new chotha database
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
  
def create_database(dbname):
  """Creates a new empty database."""
  
  conn = apsw.Connection(dbname)
  c = conn.cursor()
  query = 'CREATE TABLE "notes" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "title" VARCHAR(255) DEFAULT "A title", "date" DATETIME, "body" TEXT DEFAULT "A body", "key_list" VARCHAR(255) DEFAULT "", "source_id" INTEGER);' 
  source_fields = get_source_fields(include_column_type=True)
  query += 'CREATE TABLE "sources" ('
  query += '"%s" %s' %(source_fields[0][0], source_fields[0][1]) 
  for n in range(1,len(source_fields)):
    query += ', "%s" %s' %(source_fields[n][0], source_fields[n][1])
  query += ');'
  query += 'CREATE TABLE "keywords" ("id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "name" VARCHAR(255));'
  query += 'CREATE TABLE "keywords_notes" ("keyword_id" INTEGER, "note_id" INTEGER, PRIMARY KEY (keyword_id, note_id));'
  query += """CREATE TRIGGER notesource1 
  AFTER UPDATE OF title ON sources 
  BEGIN
    UPDATE notes SET title = new.title || ' (' || new.citekey || ')' WHERE source_id = new.id;
  END;"""
  query += """CREATE TRIGGER notesource2 
  AFTER UPDATE OF citekey ON sources 
  BEGIN
    UPDATE notes SET title = new.title || ' (' || new.citekey || ')' WHERE source_id = new.id;
  END;"""
  
  c.execute(query)
  

def copy_over_notes(rriki_db, chotha_db):
  """Copy over all the notes as is, dropping the created_at and updated_at columns."""
  conn = apsw.Connection(chotha_db)
  c = conn.cursor()
  query = 'ATTACH DATABASE ? AS rriki'
  c.execute(query, (rriki_db,))
  query = "INSERT INTO notes (id,date,title,body) SELECT id,date,title,body FROM rriki.notes"
  c.execute(query)

def copy_over_sources(rriki_db, chotha_db):
  """Copy over all the sources as is, dropping the created_at, updated_at and url columns"""

  conn = apsw.Connection(chotha_db)
  c = conn.cursor()
  query = 'ATTACH DATABASE ? AS rriki'
  c.execute(query, (rriki_db,))
  query = """INSERT INTO sources (
  id,abstract,address,author,booktitle,chapter,citekey,edition,editor,
  howpublished,institution,journal,month,number,organization,pages,publisher,
  school,series,title,source_type,volume,year)
  SELECT id,abstract,address,author,booktitle,chapter,citekey,edition,editor,
  howpublished,institution,journal,month,number,organization,pages,publisher,
  school,series,title,source_type,volume,year 
  FROM rriki.sources"""
  c.execute(query)

def create_source_notes(rriki_db, chotha_db):
  """For each source, create a new note and fill in the source_id appropriately
  set the note date as the source created_at date and the note title as the paper
  title + citekey
  => note and source ids remain the same, but now we have a bunch of extra notes at the end"""

  conn = apsw.Connection(chotha_db)
  c = conn.cursor()
  query = 'ATTACH DATABASE ? AS rriki'
  c.execute(query, (rriki_db,))
  query = """INSERT INTO notes (date,title,body,source_id)
  SELECT created_at,(title||' (')||(citekey||')'),body,id 
  FROM rriki.sources"""
  c.execute(query)

def transfer_keywords(rriki_db, chotha_db):
  """
  * Go through all rriki keywords, break them up by path separator and comma to
    build a list of component keywords matched to the original keyword
  * At the same time insert the component keywords into chotha
  """

  conn = apsw.Connection(chotha_db)
  c = conn.cursor()
  query = 'ATTACH DATABASE ? AS rriki'
  c.execute(query, (rriki_db,))
  
  #First build up a list of keywords we have in the database
  #key = rriki keyword id, value = component keywords
  print 'Building keyword list'
  component_keywords = {}
  bindings = []#Needs to be a list of tuples (to put into executemany)
  query = "SELECT rriki.keywords.id, rriki.keywords.path_text FROM rriki.keywords"
  for row in c.execute(query):
    keywords = []
    kw_frags = row[1].split(',')
    for kw_fr in kw_frags:
      kws = kw_fr.split('/')
      for kw in kws:
        kw = kw.strip()
        if kw != '':
          keywords.append(kw)
          bindings.append((kw,kw))
    component_keywords[row[0]] = keywords
  
  print 'Inserting keywords'
  query = """INSERT INTO keywords (name) SELECT ? WHERE NOT EXISTS 
  (SELECT 1 FROM keywords WHERE name LIKE ?);"""
  c.executemany(query, bindings)
  
  return component_keywords

def note_keywords(rriki_db, chotha_db, component_keywords):
  """
  * Read in the list of rriki keyword ids for each note, find the relevant component
    keywords and insert the pairs into chotha's keywords_notes
  """

  conn = apsw.Connection(chotha_db)
  c = conn.cursor()
  query = 'ATTACH DATABASE ? AS rriki'
  c.execute(query, (rriki_db,))
  
  print 'Associating keywords with notes'
  query = """
  SELECT rriki.notes.id, group_concat(rriki.keywords.id) AS kwds FROM rriki.notes 
    INNER JOIN rriki.keywords_notes ON rriki.keywords_notes.note_id = rriki.notes.id 
    INNER JOIN rriki.keywords on rriki.keywords_notes.keyword_id = rriki.keywords.id 
    GROUP BY rriki.notes.id
  """
  bindings1 = []
  bindings2 = []
  for row in c.execute(query):
    nid = row[0]
    keylist = set([])
    kidlist = row[1].split(',')
    for kid in kidlist:
      for kwd in component_keywords[int(kid)]:
        keylist.add(kwd)
    kl = ''
    for kwd in keylist:
      bindings1.append((nid,kwd))
      kl += ',' + kwd
    if kl != '':
      kl = kl[1:] #Get rid of leading comma
    bindings2.append((kl,nid)) #key_list, note.id
    
  print 'Performing SQL insert'  
  query = """INSERT OR IGNORE INTO keywords_notes (keyword_id,note_id) 
  SELECT keywords.id,? FROM keywords WHERE keywords.name LIKE ?
  """ #bindings -> note_id, keyword
  c.executemany(query, bindings1)

  print 'Inserting note key_list string'
  query = """UPDATE notes SET key_list=? WHERE id=?
  """ #bindings -> key_list, note_id
  c.executemany(query, bindings2)

def source_keywords(rriki_db, chotha_db, component_keywords):
  """
  * Read in the list of rriki keyword ids for each source, find the relevant component
    keywords and insert the pairs into chotha's keywords_notes
  """

  conn = apsw.Connection(chotha_db)
  c = conn.cursor()
  query = 'ATTACH DATABASE ? AS rriki'
  c.execute(query, (rriki_db,))
  
  print 'Associating keywords with sources'
  query = """
  SELECT rriki.sources.id, group_concat(rriki.keywords.id) AS kwds FROM rriki.sources 
    INNER JOIN rriki.keywords_sources ON rriki.keywords_sources.source_id = rriki.sources.id 
    INNER JOIN rriki.keywords on rriki.keywords_sources.keyword_id = rriki.keywords.id 
    GROUP BY rriki.sources.id
  """
  bindings1 = []
  bindings2 = []
  for row in c.execute(query):
    sid = row[0]
    keylist = set([])
    kidlist = row[1].split(',')
    for kid in kidlist:
      for kwd in component_keywords[int(kid)]:
        keylist.add(kwd)
    kl = ''
    for kwd in keylist:
      bindings1.append((kwd,sid))
      kl += ',' + kwd
    if kl != '':
      kl = kl[1:] #Get rid of leading comma
    bindings2.append((kl,sid)) #key_list, note.id

  print 'Performing SQL insert'  
  query = """INSERT OR IGNORE INTO keywords_notes (keyword_id,note_id) 
  SELECT keywords.id,notes.id FROM keywords,notes WHERE 
  keywords.name LIKE ? AND notes.source_id = ?
  """ #bindings -> keyword, source_id
  c.executemany(query, bindings1)

  print 'Inserting note key_list string'
  query = """UPDATE notes SET key_list=? WHERE source_id=?
  """ #bindings -> key_list, note_id
  c.executemany(query, bindings2)


if __name__ == "__main__":
  if len(sys.argv) > 2:
    rriki_db = sys.argv[1]
    chotha_db = sys.argv[2]
  else:
    exit()

  print 'converting ' + rriki_db + ' to ' + chotha_db
  try:
    os.remove(chotha_db)
  except:
    pass
  create_database(chotha_db)
  print 'Transferring notes'
  copy_over_notes(rriki_db, chotha_db)
  print 'Transferring sources'
  copy_over_sources(rriki_db, chotha_db)
  print 'Creating source notes'
  create_source_notes(rriki_db, chotha_db)   
  component_keywords = transfer_keywords(rriki_db, chotha_db)
  note_keywords(rriki_db, chotha_db, component_keywords)
  source_keywords(rriki_db, chotha_db, component_keywords)
