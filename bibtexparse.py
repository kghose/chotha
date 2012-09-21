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