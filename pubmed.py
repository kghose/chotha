"""Get record from pubmed. 
Modified from a script by Simon Greenhill. http://simon.net.nz/
"""
import urllib, logging
from xml.dom import minidom
module_logger = logging.getLogger('chotha.pubmed')

def pubmed_id_from_query(query, email='kaushik.ghose@gmail.com', tool='Chotha', database='pubmed'):
  """This is not designed as a search tool. This is designed to take in a unique query and return a single result.
  The query can be a title, a pubmed id or a doi.

  pubmed's esearch can be forced to do a title search by setting 'field' to be 'titl'

  Pubmed's search will automatically detect doi and uids

  Now, pubmed uid's are numbers and the doi prefix is numeric (http://www.doi.org/handbook_2000/appendix_1.html#A1-A).
  (In fact All DOI names start with "10." (http://www.doi.org/handbook_2000/enumeration.html#2.2))

  Therefore we interpret any query that does not begin with a number as a title query. This will not really fail for
  queries for titles that begin with numbers, for example if we search for

  7/10 Problems treated in collaboration and nursing diagnostics

  Our code here will not flag it as a [Title] search, BUT clever entrez will do a title search for us. The fear then is
  that the results won't be unique - in principle - but in practice titles starting with numbers are rare enough that
  the results will highly likely be unique.
  """

  #Clean up query string
  query = query.strip()

  #Setup basic parameters
  params = {
    'db':database,
    'tool':tool,
    'email':email,
    'term':query,
    'retmax':1
  }

  if not len(query):
    module_logger.warning('Empty query')
  else:
    if query[0].isalpha(): #For a title search we explicitly set the search field to be title
      params['field'] =  'titl'

  #Construct the query string and retrieve the results
  url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?' + urllib.urlencode(params)
  module_logger.debug(url)
  data = urllib.urlopen(url).read()
  xmldoc = minidom.parseString(data)

  # Extract the PubMed ID from the result
  ids = xmldoc.getElementsByTagName('Id')
  if not len(ids):
    pmid = None
    module_logger.warning('No record found')
  else:
    pmid = ids[0].childNodes[0].data

  return pmid


def citation_from_pmid(pmid, email='kaushik.ghose@gmail.com', tool='Chotha', database='pubmed'):
  # remove unwanted parameters
  params = {
  'db':database,
  'id':pmid,
  'tool':tool,
  'email':email,
  'retmode':'xml'
  }
  # get citation info:
  url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?' + urllib.urlencode(params)
  data = urllib.urlopen(url).read()
  return data

def citation_from_query(query, email='kaushik.ghose@gmail.com', tool='Chotha', database='pubmed'):
  pmid = pubmed_id_from_query(query, email, tool, database)
  if pmid is None:
    return None
  else:
    return citation_from_pmid(pmid, email, tool, database)

def gebtn(doc,name):
  try:
    return doc.getElementsByTagName(name)[0].childNodes[0].data
  except:
    return ''
  
def parse_pubmed_xml_to_source(xml, source=None):
  """Parses XML returned from efetch into a source dictionary that we can
  save into the database"""
  if not source: source = {}

  xmldoc = minidom.parseString(xml)
  
  source['title'] = gebtn(xmldoc,'ArticleTitle') 
  source['abstract'] = gebtn(xmldoc,'AbstractText')
  
  authors = xmldoc.getElementsByTagName('AuthorList')[0]
  authors = authors.getElementsByTagName('Author')
  authortext = ''
  for author in authors:
    LastName = gebtn(author,'LastName')
    ForeName = gebtn(author,'ForeName')
    authortext += '%s, %s\n' % (LastName, ForeName)
  source['author'] = authortext
    
  journalinfo = xmldoc.getElementsByTagName('Journal')[0]
  source['journal'] = gebtn(journalinfo,'Title')
  journalinfo = journalinfo.getElementsByTagName('JournalIssue')[0]
  source['volume'] = gebtn(journalinfo,'Volume')
  source['number'] = gebtn(journalinfo,'Issue')
  source['year'] = gebtn(journalinfo,'Year')
  source['month'] = gebtn(journalinfo,'Month')

  source['pages'] = gebtn(xmldoc,'MedlinePgn')
  
  aid = xmldoc.getElementsByTagName('ArticleId')
  for a in aid:
    if a.attributes['IdType'].value == 'doi':
      source['doi'] = a.childNodes[0].data
  
  source['source_type'] = 'article'
  return source

if __name__ == '__main__':
  from sys import argv, exit
  if len(argv) == 1:
    print 'Usage: %s <query>' % argv[0]
    print ' e.g. %s 10.1038/ng1946' % argv[0]
  else:
    #citation = citation_from_query(argv[1])
    pmid = pubmed_id_from_query(argv[1])
    #print pmid
    citation = citation_from_pmid(pmid)
    print citation
    #for line in text_output(citation):
    #  print line