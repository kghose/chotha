"""
A filter to let math expressions in latex emerge unscathed through markdown
Based on the markdown extension documents and python-ascii math at
https://github.com/favalex/python-asciimathml/blob/e4c808d096f3ae270f5305b944a66c31a37dc853/mdx_asciimathml.py

The filename has to start with 'mdx_' and the rest of the name is what must be
put in the 'extensions' list when markdown is invoked i.e.

  md = markdown.Markdown(extensions=['chothamathml']).convert

A bit more sophisticated than the regexp search and hide technique I used in RRiki
"""

import re, markdown

regexp = r"""
^(.*) #Markdown regex needs to start with this
\$(.*?)\$ #Non greedy match anything between $ sign 
(.*)$ #Needs to end with this
"""

class escapeLaTeXExtension(markdown.Extension):
  def __init__(self, configs):
    pass
  
  def extendMarkdown(self, md, md_globals):
    self.md = md
    """The name of this extension is escapeLaTeX and it is inserted at the
    head of all the markdown operations (_begin)."""
    md.inlinePatterns.add('escapeLaTeX', escapeLaTeXPattern(md), '_begin')
      
  def reset(self):
    pass

class escapeLaTeXPattern(markdown.inlinepatterns.Pattern):
  def getCompiledRegExp(self):
    """The regexp is meant to run multiline mode and we use VERBOSE because we
    commented the regexp so nicely."""
    return re.compile(regexp, re.M | re.VERBOSE)
    
  def handleMatch(self, m):
    """Markdown regexp processes the whole block, and so our regexp match is
    group(2) with group(1) and group(3) being the leading and trailing."""
    el = markdown.etree.Element('span')
    el.text = markdown.AtomicString("`" + m.group(2) + "`")
    return el

def makeExtension(configs=None):
    return escapeLaTeXExtension(configs=configs)