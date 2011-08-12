"""This is a dangerous, but needed, purge. The keywords from rriki are
cluttering up everything. So I'm just going to remove keywords from all notes
where rriki imported is one of the keywords."""

import apsw

dbname = "/Users/kghose/research/Library/research_notes_chotha.sqlite3"
conn = apsw.Connection(dbname)
c = conn.cursor()
c.execute('SELECT id FROM notes WHERE key_list LIKE "%rriki imported%"')
ids = c.fetchall()
c.execute('BEGIN')
c.executemany('DELETE FROM keywords_notes WHERE note_id=?', ids)
c.execute('END')
c.execute('DELETE FROM keywords WHERE id NOT IN (SELECT keyword_id FROM keywords_notes)')


#dbq('DELETE FROM keywords_notes WHERE note_id=?', (note_id,))