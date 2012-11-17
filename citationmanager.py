"""Functions to export sources to particular formats"""
from xml.dom import minidom
import re

def parse_name_field(text):
  """Utility function used to extract names of authors and editors from a text
  field."""
  name_list = []
  if text != '':
    for au_line in text.split("\n"):
      au_line = au_line.strip()
      if au_line == '': 
        continue #Ignore empty lines
      name = {'first': 'none', 'last': 'none'}
      name_fragments = au_line.split(',')
      name['last'] = name_fragments[0].strip()
      if len(name_fragments) > 1:
        name['first'] = name_fragments[1].strip()
      name_list.append(name)
  return name_list    

# Bibtex -----------------------------------------------------------------------
def parse_bibtex_to_source(text, source={}):
  def parse_bibtex_authors(autext):
    """Take the bibtex author list and convert it to line separated list."""
    ausep = re.compile(r'(.*?)(?: and |$)')
    au_list = ausep.findall(autext)
    s_au_text = ""
    for au in au_list:
      if au is not "":
        s_au_text += au + '\n'
    return s_au_text

  def reverse_bibtexescape(text):
    """Unescape characters that have been escaped in BibTeX to prevent the
    backslash explosion."""
    unescape = lambda match: match.group(1).strip('\\')
    esc = re.compile(r'(\\[&|%]+?)')
    if text is not None:
      text = esc.sub(unescape,text)
    return text

  text = reverse_bibtexescape(text)

  typeparse = re.compile(r'@(.+?)\{(.*?),')
  kvparse = re.compile(r',[\s]*(.+?)[\s]*=[\s]*\{(.+?)\}', re.DOTALL)#DOTALL includes newlines in .

  typ = typeparse.findall(text)
  if len(typ):
    source['source_type'] = typ[0][0].strip()
    source['citekey'] = typ[0][1].strip()

  for kv in kvparse.findall(text):
    source[kv[0]] = kv[1]

  source['author'] = parse_bibtex_authors(source['author'])

  return source

def source_to_bibtex(sources, include_abstract=True):
  """Given a list of sources convert it to bibtex."""
  def add_authors(source):
    name_text = ''
    nl = parse_name_field(source['author'])
    for n,fn in enumerate(nl):
      name_text += fn['last'] + "," + fn['first']
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

  excluded_keys = ['source_type', 'author', 'citekey', 'id']
  if not include_abstract:
    excluded_keys += ['abstract']
  bibtex = ""
  for source in sources:
    bibtex += "@%s{%s,\n" %(source['source_type'], source['citekey'])
    for key in source.keys():
      if key not in excluded_keys: #id screws up jabref, for one, and is not a standard bibtex field
        if source[key] != '':
          bibtex += "%s = {{%s}},\n" %(key, source[key])
      elif key == 'author':
        bibtex += "author = {%s},\n" %add_authors(source)
    bibtex += "}\n\n"
  bibtex = bibtexescape(bibtex)

  return bibtex


# Citation exports -------------------------------------------------------------

def export_BibTeX(fname='sources.bib', sources=None):
  """Export all the sources to the named bib file."""
  import codecs

  bibtex = "#This file is automatically created by Chotha.\n\n\n"
  bibtex += source_to_bibtex(sources, include_abstract=False)
  bibtex += "\n\n"
  codecs.open(fname,'wb','utf-8').write(bibtex)
  return len(sources)


def export_MSWord_XML(fname='/Users/kghose/Documents/Microsoft User Data/Sources.xml', sources=None):
  """Add citations in the sources list to the MS Word Sources.xml file. Skip
  adding citations whose citekey already exists in the file. New citations are
  appended to the existing file."""
  import zipfile

  Source_type_xml = {
    "article" : 'JournalArticle', 
    "book" : 'Book', 
    "booklet" : 'BookSection', 
    "collection" : 'BookSection', 
    "conference" : 'BookSection',
    "inbook" : 'BookSection', 
    "incollection" : 'BookSection', 
    "inproceedings" : 'ConferenceProceedings', 
    "manual" : 'Book', 
    "mastersthesis" : 'Report',
    "misc" : 'Book', 
    "patent" : 'Book', 
    "phdthesis" : 'Report', 
    "proceedings" : 'ConferenceProceedings', 
    "techreport" : 'Book', 
    "unpublished" : 'Book'}
  
  def read_and_parse_MSWord_master_source_XML(fname='/Users/kghose/Documents/Microsoft User Data/Sources.xml'):
    """Given the name of a MSWord source list xml file, read it in, parse out the 
    citekeys and return us the file contents and a list of citekeys present
    in the file."""
    def create_new_master_source_XML(fname):
      print 'Will get parse error on reading this file due to ExpatError, need to clean up namespace thingy'
      impl = minidom.getDOMImplementation()
      namespaceuri = "http://schemas.openxmlformats.org/officeDocument/2006/bibliography"
      newdoc = impl.createDocument(namespaceuri, "b:Sources", None)
      return newdoc
      #<?xml version=\"1.0\" ?>\n" +
      #          "<b:Sources SelectedStyle=\"\" xmlns:b=\"http://schemas.openxmlformats.org/officeDocument/2006/bibliography\" xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/bibliography\">"
                
    citekey_list = []
    import os
    if os.path.exists(fname):
      doc = minidom.parse(fname)
    else:
      print 'Source.xml file absent. Creating new.'
      doc = create_new_master_source_XML(fname)
      
    xmldoc = doc.documentElement
    for ref in xmldoc.getElementsByTagName("b:Source"):
      try:
        ck = ref.getElementsByTagName("b:Tag")[0].childNodes[0].wholeText
        citekey_list.append(ck)
      except:
        print 'Cheap way to not do proper error checking'
      #print 'Hi'
      #print ref.attributes["Tag"].value
    return doc, citekey_list

  def save_MSWord_master_source_XML(doc, fname='/Users/kghose/Documents/Microsoft User Data/Sources.xml'):
    #print doc.documentElement.toprettyxml(encoding='utf-8')
    #doc.documentElement.writexml(open(fname,'w'), encoding='utf-8')
    
    #doc.writexml(open(fname,'wb'), encoding='utf-8')
    import codecs
    doc.writexml(codecs.open(fname,'wb','utf-8'), encoding='utf-8')

  def read_and_parse_MSWord_XML(fname='Sandbox/test.docx'):
    """Given the name of a MSWord source list xml file, read it in, parse out the 
    citekeys and return us the file contents and a list of citekeys present
    in the file."""
    #xml = open(fname).read()
    xmlsources = []
    #with zipfile.ZipFile(fname) as myzip:
    myzip = zipfile.ZipFile(fname)
    xmlsources = myzip.read('customXml/item1.xml')
    
    citekey_list = []
    max_refo = 1
    doc = minidom.parseString(xmlsources)
    xmldoc = doc.documentElement
    print xmldoc.toprettyxml()
    for ref in xmldoc.getElementsByTagName("b:Source"):
      try:
        ck = ref.getElementsByTagName("b:Tag")[0].childNodes[0].wholeText
        citekey_list.append(ck)
      except:
        print 'Cheap way to not do proper error checking'
      
      refo = int(ref.getElementsByTagName("b:RefOrder")[0].childNodes[0].wholeText)
      max_refo = refo if refo > max_refo else max_refo
      #print ref.attributes["Tag"].value
    return doc, citekey_list, max_refo
    
  def save_MSWord_XML(doc, fname='Sandbox/test.docx'):
    #with zipfile.ZipFile(fname, 'w') as myzip:
    myzip = zipfile.ZipFile(fname, 'a',compression=zipfile.ZIP_DEFLATED)
    myzip.writestr('customXml/test1.xml', doc.toxml().encode('utf-8'))
    myzip.close()
      
  def add_source_to_XML(doc, source, refo=None):
    """If max_refo is not none then we assume we are messing with the document 
    ref file and we need to put in the reforder tag"""
    def add_element(tag, value, doc, child):
      tag = doc.createElement(tag)
      child.appendChild(tag)
      if value is not None and value != '':
        tagtext = doc.createTextNode(value)
        tag.appendChild(tagtext)
      return doc, tag
    
    def add_authors(doc, cite, source):
      nl = parse_name_field(source['author'])
      doc, tag = add_element('b:Author', None, doc, cite)
      doc, tag = add_element('b:Author', None, doc, tag)
      doc, nltag = add_element('b:NameList', None, doc, tag)
      for fn in nl:
        doc,ptag = add_element('b:Person', None, doc, nltag)
        doc,tag = add_element('b:Last', fn['last'], doc, ptag)
        doc,tag = add_element('b:First', fn['first'], doc, ptag)
      return doc
      
    cite = doc.createElement('b:Source')
    doc.firstChild.appendChild(cite)

    doc,tag = add_element('b:Tag', source['citekey'], doc, cite)
    doc,tag = add_element('b:SourceType', Source_type_xml[source['source_type']], doc, cite)
    if source['source_type'] == 'mastersthesis':
      doc,tag = add_element('b:ThesisType', 'Masters Thesis', doc, tag)
    elif source['source_type'] == 'phdthesis':
      doc,tag = add_element('b:ThesisType', 'PhD Thesis', doc, tag)
    doc = add_authors(doc, cite, source)
    doc,tag = add_element('b:ConferenceName', source['booktitle'], doc, cite)
    doc,tag = add_element('b:Edition', source['edition'], doc, cite)
    doc,tag = add_element('b:JournalName', source['journal'], doc, cite)
    doc,tag = add_element('b:Month', source['month'], doc, cite)
    doc,tag = add_element('b:Issue', source['number'], doc, cite)
    doc,tag = add_element('b:Pages', source['pages'], doc, cite)
    doc,tag = add_element('b:Publisher', source['publisher'], doc, cite)
    doc,tag = add_element('b:Institution', source['school'], doc, cite)
    doc,tag = add_element('b:Title', source['title'], doc, cite)
    doc,tag = add_element('b:Volume', source['volume'], doc, cite)
    doc,tag = add_element('b:Year', str(source['year']), doc, cite)
    if refo is not None:
      doc,tag = add_element('b:RefOrder', str(refo), doc, cite)

    return doc
    
  def add_sources_to_XML(doc, sources, citekey_list, max_refo=None):
    """If max_refo is NOT none then we assume we are messing with the document 
    ref file and we need to put in the reforder tag"""
    refo = max_refo
    ref_count = 0
    for source in sources:
      if source['citekey'] not in citekey_list:
        if refo is not None:
          refo += 1
        doc = add_source_to_XML(doc, source,refo)
        ref_count += 1
    return doc, ref_count
  
  doc, citekey_list = read_and_parse_MSWord_master_source_XML(fname)
  doc, refcount = add_sources_to_XML(doc, sources, citekey_list)
  save_MSWord_master_source_XML(doc,fname)
  return refcount


def export_RIS(fname, sources):
  """This exports to the nice and flat RIS format which endnote can import
    Documentation was obtained from
    http://en.wikipedia.org/wiki/RIS_%28file_format%29"""
  def ris_authors(source):
    ris = ''
    aul = parse_name_field(source['author'])
    for au in aul:
      ris += "AU  - %s, %s\n" %(au['last'], au['first'])
    return ris
  
  #Field tags that are exported as is
  Field2RISTag = {
    #"abstract" text, 
    "address" : 'AD', 
    #"author" varchar(255), 
    "booktitle" : 'TI', 
    #"chapter" varchar(255), 
    #"citekey" varchar(255), 
    #"edition" varchar(255), 
    "editor" : 'ED', 
    #"filing_index" varchar(255), 
    #"howpublished" varchar(255), 
    #"institution" varchar(255), 
    "journal" : 'JF', 
    #"month" varchar(255), #Handled through Y1
    "number" : 'IS', 
    #"organization" varchar(255), 
    #"pages" varchar(255), #Handled by SP,EP
    "publisher" : 'PB', 
    #"school" varchar(255), 
    #"series" varchar(255), 
    "title" : 'T1', 
    #"source_type" varchar(255), 
    #"url" varchar(255), 
    "volume" : 'VL', 
    #"year" integer,#Handled through Y1 
    #"body" text, "created_at" datetime, "updated_at" datetime
    }    
  # How to convert our types to RIS TY codes
  SourceType2RIS = {
    "article" : 'JOUR', 
    "book" : 'BOOK', 
    #"booklet" => 'BOOK', 
    #"collection", 
    "conference" : 'CONF',
    "inbook" : 'CHAP', 
    "incollection" : 'CONF', 
    "inproceedings" : 'CONF', 
    #"manual" => 'GEN', 
    "mastersthesis" : 'THES',
    "misc" : 'GEN', 
    "patent" : 'PAT', 
    "phdthesis" : 'THES', 
    "proceedings" : 'CONF', 
    "techreport" : 'RPRT', 
    "unpublished" : 'UNPB'
  }

  ris = ""
  for source in sources:
    ris += "TY  - %s\n" %SourceType2RIS[source['source_type']]
    for key in source.keys():
      if Field2RISTag.has_key(key):
        if source[key] != '':
          ris += "%s  - %s\n" %(Field2RISTag[key], source[key])
      
    ris += ris_authors(source)
    ris += "PY  - %04d///\n" %source['year']
    pages = source['pages'].rsplit('-')
    ris += "SP  - %s\n" %pages[0]
    ris += "EP  - %s\n" %pages[-1]    
    ris += "ER  -\n\n"
  ris += "\n\n"

  import codecs
  codecs.open(fname,'wb','utf-8').write(ris)
  return len(sources)
  
if __name__ == "__main__":
  export_MSWord_XML()