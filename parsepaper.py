#!/usr/bin/env python
import commands
import os
from pyquery import PyQuery
import urllib
import urllib2
import socket

for fn in os.listdir("papers"):
    if fn.endswith(".pdf"):
        try:
            # Title parsing (local)
            title = commands.getoutput('./pdftitle.py papers/%s' % fn)
            print fn + " : " + title
            fw = open("papers/" + fn.replace(".pdf", ".title.txt"), 'w')
            fw.write(title)
            fw.close()

            # Abstract parsing
            lookupurl = "http://ieeexplore.ieee.org/search/searchresult.jsp?" + urllib.urlencode({'queryText': title})
            page = urllib2.urlopen(lookupurl, "", 10)
            html = page.read()
            pq = PyQuery(html)
            abstract = pq('#abstract-1:first').text().encode('ascii', 'ignore')
            abstract = abstract.replace("View full abstract", "")
            fw = open("papers/" + fn.replace(".pdf", ".abstract.txt"), 'w')
            fw.write(abstract)
            fw.close()

            # Bibtex parsing
            lookupurl = "http://dblp.kbs.uni-hannover.de/dblp/Search.action?" + urllib.urlencode({'q': title})
            page = urllib2.urlopen(lookupurl, "", 10)
            html = page.read()
            start = "clip.setText('"
            end = "'); else"
            bibtex = html[html.find(start)+len(start):html.find(end)]
            bibtex = bibtex.replace(",###", ",\n    ")
            bibtex = bibtex.replace("###", " ")
            bibtex = bibtex.replace("crossref", "xcrossref")
            bibidentifier = bibtex[bibtex.find("{")+len("{"):bibtex.find(",")]
            fw = open("papers/" + fn.replace(".pdf", ".bib"), 'w')
            if (len(bibidentifier) > 1):
                bibtex = bibtex.replace(bibidentifier, fn)
                fw.write(bibtex)
            fw.close()
        except (socket.timeout) as err:
            print "Connection error"

        break
