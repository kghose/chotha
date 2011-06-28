"""
A filter to let asciimath and latexmath stuff emerge unscathed through markdown
Based on the markdown extension documents and
python-ascii math
https://github.com/favalex/python-asciimathml/blob/e4c808d096f3ae270f5305b944a66c31a37dc853/mdx_asciimathml.py

A bit more sophisticated than the regexp search and hide tecqnique I used in RRiki
"""

import re, markdown

class ASCIIMathMLExtension(markdown.Extension):
    def __init__(self, configs):
        pass

    def extendMarkdown(self, md, md_globals):
        self.md = md

        RE = re.compile(r'^(.*)\$\$([^\$]*)\$\$(.*)$', re.M) # $$ a $$

        md.inlinePatterns.add('', ASCIIMathMLPattern(RE), '_begin')

    def reset(self):
        pass

class ASCIIMathMLPattern(markdown.inlinepatterns.Pattern):

    def handleMatch(self, m):
        el = markdown.etree.Element('span')
        el.text = "$" + m.group(2) + "$"
        return el

def makeExtension(configs=None):
    return ASCIIMathMLExtension(configs=configs)