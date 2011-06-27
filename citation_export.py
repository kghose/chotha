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
      name_fragments = au_line.split(',')
      name = {}
      frag = name_fragments[0].strip()
      name['last'] = frag if frag != '' else 'none'
      frag = name_fragments[1].strip()
      name['first'] = frag if frag != '' else 'none'
      name_list.append(name)
  return name_list    

def export_MSWord_XML(sources=None):
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
    doc = minidom.parseString(xmlsources)
    xmldoc = doc.documentElement
    print xmldoc.toprettyxml()
    for ref in xmldoc.getElementsByTagName("b:Source"):
      try:
        ck = ref.getElementsByTagName("b:Tag")[0].childNodes[0].wholeText
        citekey_list.append(ck)
      except:
        print 'Cheap way to not do proper error checking'
      #print 'Hi'
      #print ref.attributes["Tag"].value
    return doc, citekey_list
    
  def save_MSWord_XML(doc, fname='Sandbox/test.docx'):
    #with zipfile.ZipFile(fname, 'w') as myzip:
    myzip = zipfile.ZipFile(fname, 'a',compression=zipfile.ZIP_DEFLATED)
    myzip.writestr('customXml/test1.xml', doc.documentElement.toxml())
    myzip.close()
      
  def add_source_to_XML(doc, source):
    """Add this source to the existing document."""
    def add_element(tag, value, doc, child):
      tag = doc.createElement(tag)
      child.appendChild(tag)
      if value != None:
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
    return doc
    
  def add_sources_to_XML(doc, sources, citekey_list):
    for source in sources:
      if source['citekey'] not in citekey_list:
        doc = add_source_to_XML(doc, source)
    return doc
  
#  doc, citekey_list = read_and_parse_MSWord_master_source_XML()
  #doc = add_source_to_XML(doc, source)
#  save_MSWord_master_source_XML(doc)

  doc, citekey_list = read_and_parse_MSWord_master_source_XML()
  doc = add_sources_to_XML(doc, sources, citekey_list)
  save_MSWord_master_source_XML(doc)

if __name__ == "__main__":
  export_MSWord_XML(sources=None)