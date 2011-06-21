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

"""
* Create a new chotha database
"""
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
  
"""
* Copy over all the notes as is, dropping the created_at and updated_at columns
"""
def copy_over_notes(rriki_db, chotha_db):
  conn = apsw.Connection(chotha_db)
  c = conn.cursor()
  query = 'ATTACH DATABASE ? AS rriki'
  c.execute(query, (rriki_db,))
  query = "INSERT INTO notes (id,date,title,body) SELECT id,date,title,body FROM rriki.notes"
  c.execute(query)

"""
* Copy over all the sources as is, dropping the created_at, updated_at and url columns
"""
def copy_over_sources(rriki_db, chotha_db):
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

"""
* For each source, create a new note and fill in the source_id appropriately
set the note date as the source created_at date and the note title as the paper
title + citekey
=> note and source ids remain the same, but now we have a bunch of extra notes at the end
"""
def create_source_notes(rriki_db, chotha_db):
  conn = apsw.Connection(chotha_db)
  c = conn.cursor()
  query = 'ATTACH DATABASE ? AS rriki'
  c.execute(query, (rriki_db,))
  query = """INSERT INTO notes (date,title,body,source_id)
  SELECT created_at,(title||'(')||(citekey||')'),body,id 
  FROM rriki.sources"""
  c.execute(query)


"""
* For each note, grab the keywords
   * For each keyword, use the path to separate out the keywords into components words.
   *  Keywords with commas - each part is a separate keyword.
   * Associate each keyword with note
* For each source, grab the keywords
   * For each keyword, use the path to separate out the keywords into components words.
   *  Keywords with commas - each part is a separate keyword.
   * Find the note that goes with the source (source ids are conserved) and associate the keywords with that note

"""

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
