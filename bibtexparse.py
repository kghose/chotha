"""Contains methods to parse BibTeX. Can be used to get citations from things
like google scholar, for example"""
import re

def parse_bibtex_to_source(text, source={}):
  typeparse = re.compile(r'@(.+?)\{')
  kvparse = re.compile(r',[\s]*(.+?)[\s]*=[\s]*\{(.+?)\}')

  typ = typeparse.findall(text)
  if len(typ):
    source['source_type'] = typ[0].strip()

  for kv in kvparse.findall(text):
    source[kv[0]] = kv[1]

  return source

def source_to_bibtex(sources):
  """Given a list of sources convert it to bibtex."""
  def add_authors(source):
    name_text = ''
    nl = parse_name_field(source['author'])
    for n,fn in enumerate(nl):
      name_text += fn['first'] + " " + fn['last']
      if n < len(nl) - 1:
        name_text += " and "
    return name_text

  def bibtexescape(text):
    """This method escapes characters from the field that cause problems for latex."""
    if text is not None:
      chars = ['%', '&']
      for c in chars:
        esc = re.compile(c + r'+?')
        text = esc.sub('\\'+c,text)
    return text

  bibtex = ""
  for source in sources:
    bibtex += "@%s{%s,\n" %(source['source_type'], source['citekey'])
    for key in source.keys():
      if key not in ['source_type', 'author', 'citekey', 'abstract', 'id']: #id screws up jabref, for one, and is not a standard bibtex field
        if source[key] != '':
          bibtex += "%s = {%s},\n" %(key, source[key])
      elif key == 'author':
        bibtex += "author = {%s},\n" %add_authors(source)
    bibtex += "}\n\n"
  bibtex = bibtexescape(bibtex)

  return bibtex
