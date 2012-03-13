"""When I was young, in over enthusiasm I used to import pubmed keywords into
the notes. This, of course, absolutely screws up my keyword scheme. I pushed the
keywords to the text so that they no longer clutter up my keywords list, but
now that I'm playing around with full text tagging, those inane Pubmed keywords 
completely screup everything. So now I'm trying to do the tricky thing of
going back and removing the keywords text."""

import apsw

def remove_pubmed_keyword_block(text):
  new_lines = []
  lines = text.split('\n')
  n = 0
  while n < len(lines):
    new_lines.append(lines[n])
    if lines[n] == 'Keywords' and n + 1 < len(lines):
      if lines[n+1] == '-------' and n + 2 < len(lines):
        if lines[n+2].startswith('* '):
          new_lines.pop()
          n += 2
          while lines[n].startswith('* '):
            n += 1
            if n == len(lines):
              break
          n -= 1
    n += 1
    
  return "\n".join(new_lines)

def remove_pubmed_keyword_block_v2(text):
  """Because I was very clever and did it in different ways."""
  new_lines = []
  lines = text.split('\n')
  n = 0
  while n < len(lines):
    new_lines.append(lines[n])
    if lines[n] == '#Keywords#' and n + 1 < len(lines):
        if lines[n+1].startswith('* '):
          new_lines.pop()
          n += 1
          while lines[n].startswith('* '):
            n += 1
            if n == len(lines):
              break
          n -= 1
    n += 1
    
  return "\n".join(new_lines)
  
dbname = "/Users/kghose/research/Library/research_notes_chotha.sqlite3"
conn = apsw.Connection(dbname)
c = conn.cursor()
c2 = conn.cursor()
for id, body in c.execute('SELECT id,body FROM notes WHERE source_id NOT NULL'):
  print id
  body = remove_pubmed_keyword_block(body)
  body = remove_pubmed_keyword_block_v2(body)
  c2.execute('UPDATE notes SET body=? WHERE id=?', (body, id))
