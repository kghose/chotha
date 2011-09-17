"""Handles the creation and maintenance of the wordcloud."""
import apsw, re

fname = 'common-english-words-with-contractions.txt'
common_words = open(fname).read().split(',')

def get_real_words(orig_text):
  words = re.findall(r'\b[a-z]+\b', orig_text, re.I)
  words = set(words)
  return set([w.lower() for w in words if w.lower() not in common_words])

def update_word_cloud(oldtext, newtext, dbname):
  """Passed two blocks of text, corresponding to the old and new version of the
  note body, split them both into words, find out which words have been removed
  which have been added and remove/add them to the word cloud ."""
  oldwords = get_real_words(oldtext)
  newwords = get_real_words(newtext)
  words_removed = oldwords - newwords #Ain't Python cool
  words_added = newwords - oldwords #Repeat with me, ain't Python cool
  
  conn = apsw.Connection(dbname)
  c = conn.cursor()
  c.execute('BEGIN')
  for word in words_removed:
    c.execute('UPDATE wordcloud SET count=count-1 WHERE word=?', (word,)) 

  #Clean it up
  c.execute('DELETE FROM wordcloud WHERE count < 1')
    
  for word in words_added:
    c.execute('UPDATE wordcloud SET count=count+1 WHERE word=?', (word,)) 
    if conn.changes() == 0:
      c.execute('INSERT INTO wordcloud (word,count) VALUES (?,1)', (word,))
  c.execute('END')

 
def update_note(old_note, new_note, dbname): 
  update_word_cloud(old_note['body'], new_note['body'], dbname)
  
def rebuild_wordcloud(notes, dbname):
  """This could take a long, long time."""
  conn = apsw.Connection(dbname)
  c = conn.cursor()
  c.execute('DELETE FROM wordcloud')
  total = len(notes)
  unique_words = {}
  for n,note in enumerate(notes):
    words = get_real_words(note['body'])
    for word in words:
      if unique_words.has_key(word):
        unique_words[word] += 1
      else:
        unique_words[word] = 1  
    #update_word_cloud('', note['body'], dbname)
    if n % 10:
      print '%0.0f%% done' %(100.*n/total)
  
  bindings = [(word,unique_words[word]) for word in unique_words]
  #Doing a transaction is soooo much faster
  c.execute('BEGIN')
  c.executemany('INSERT INTO wordcloud (word,count) VALUES (?,?)', bindings)
  c.execute('END')
    