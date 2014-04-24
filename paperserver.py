import SimpleHTTPServer
import SocketServer
import logging
import cgi
import webactions
import json
import re
import sys
import os
import collections

source_pdf = "unknown"
source_title = "unknown"
source_abstract = "unknown"
source_bibtex = "unknown"
source_citations = []
search_citations = []
cited_pdfs = []
cited_pdfs_title = []
cited_pdfs_citation = []
cited_cited_pdfs_title = []
cited_cited_pdfs_citation = []
parsedkeywords = {}

selectedpapers = []
selectedsubpapers = []
selectedkeywords = []

newauthors = "unknown"
newtitle = "unknown"
newdate = "unknown"
newinstitute = "unknown"
newabstract = "unknown"
newconclusion = "unknown"

latextemplate = "empty"
bibtextemplate = "empty"
bibtexitems = {}

# output buffer disable to get better logging results
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)


class CustomHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def do_POST(self):
        logging.error(self.headers)
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'
                     })
        logging.error(form.list)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        global source_pdf
        global source_title
        global source_abstract
        global source_bibtex
        global source_citations
        global search_citations

        global cited_pdfs
        global cited_pdfs_citation
        global cited_pdfs_title
        global cited_cited_pdfs_citation
        global cited_cited_pdfs_title
        global parsedkeywords

        global selectedpapers
        global selectedsubpapers
        global selectedkeywords

        global newauthors
        global newtitle
        global newdate
        global newinstitute
        global newabstract
        global newconclusion

        global latextemplate
        global bibtexitems
        global bibtextemplate

        if self.path == "/action":
            for item in form.list:
                print "%s=%s" % (item.name, item.value)
                if item.name == "papertitle":
                    source_title = item.value
                    source_abstract = webactions.parseAbstract(source_title)
                    source_bibtex = webactions.parseBibtex(source_title)
                    source_citations = webactions.parseCitations(source_title)

                    citationsoutput = ""
                    for citation in source_citations:
                        citationsoutput += citation + "\n"
                        cited_pdfs_citation.append(citation)
                        title = webactions.get_first(re.compile('".*?"', re.DOTALL).findall(citation))
                        if title is None:
                            continue
                        title = title.replace('"', '')
                        cited_pdfs_title.append(title)

                    citedcitationsoutput = ""
                    for title in cited_pdfs_title:
                        try:
                            subcitations = webactions.parseCitations(title)
                            citedcitationsoutput += title + "\n"
                            for subcitation in subcitations:
                                cited_cited_pdfs_citation.append(subcitation)
                                title = webactions.get_first(re.compile('".*?"', re.DOTALL).findall(subcitation))
                                if title is None:
                                    continue
                                title = title.replace('"', '')
                                cited_cited_pdfs_title.append(title)
                                citedcitationsoutput += " - " + title + "\n"
                                #break
                            citedcitationsoutput += "\n"
                            break
                        except TypeError:
                            print "Can't parse citations for paper " + title

                    parse_keywords = webactions.parseKeywords(source_title)
                    if isinstance(parse_keywords, collections.Iterable):
                        for keyword in parse_keywords:
                            if keyword in parsedkeywords:
                                parsedkeywords[keyword] += 1
                            else:
                                parsedkeywords[keyword] = 1

                    for i, title in enumerate(cited_pdfs_title):
                        parse_keywords = {}#webactions.parseKeywords(title)
                        if isinstance(parse_keywords, collections.Iterable):
                            for keyword in parse_keywords:
                                if keyword in parsedkeywords:
                                    parsedkeywords[keyword] += 1
                                else:
                                    parsedkeywords[keyword] = 1
                            #break
                    for i, title in enumerate(cited_cited_pdfs_title):
                        parse_keywords = {} #webactions.parseKeywords(title)
                        if isinstance(parse_keywords, collections.Iterable):
                            for keyword in parse_keywords:
                                if keyword in parsedkeywords:
                                    parsedkeywords[keyword] += 1
                                else:
                                    parsedkeywords[keyword] = 1

                    keywordsoutput = ""
                    for key in parsedkeywords:
                        keywordsoutput += "%d : %s\n" % (parsedkeywords[key], key)

                    self.wfile.write(json.dumps({'message': "Properties parsed from paper", 'result': "TITLE:\n%s\n\nABSTRACT:\n%s\n\nBIBTEX:\n%s\n\nCITATIONS:\n%s\n\nCITED CITATIONS:\n%s\nKEYWORDS:\n%s\n\n" % (source_title, source_abstract, source_bibtex, citationsoutput, citedcitationsoutput, keywordsoutput)}))
                    continue
                if item.name == "showinfo":
                    output = ""
                    for i, title in enumerate(cited_pdfs_title):
                        output += '<input type="checkbox" class="selectpapers" name="selectpapers[]" value="%d" /> %s <br />' % (i, title)
                        #print output
                    for i, title in enumerate(cited_cited_pdfs_title):
                        output += '<input type="checkbox" class="selectsubpapers" name="selectsubpapers[]" value="%d" /> %s <br />' % (i, title)
                        #print output

                    output += '<div id="wordcloud" style="border:1px solid #f00;height:500px;width:800px;">'
                    for key in parsedkeywords:
                        output += '<span data-weight="%d">%s</span>' % (parsedkeywords[key], key)
                    output += '</div>'
                    self.wfile.write(json.dumps({'message': output, 'result': ""}))
                    continue
                if item.name == "selectpapers":
                    selectedpapers = item.value.split(",")
                    continue
                if item.name == "selectsubpapers":
                    selectedsubpapers = item.value.split(",")
                    continue
                if item.name == "papersselected":
                    output = ""
                    output += '<input id="newtitle" class="form-control" placeholder="Title of generated paper" type="text" />'
                    output += '<input id="newauthors" class="form-control" placeholder="Authors of generated paper" type="text" />'
                    output += '<input id="newdate" class="form-control" placeholder="Date of generated paper" type="text" />'
                    output += '<input id="newinstitute" class="form-control" placeholder="Institute of generated paper" type="text" />'
                    output += '<textarea id="newabstract" name="newabstract" class="form-control" rows="10">%s</textarea>' % source_abstract
                    output += '<textarea id="newconclusion" name="newconclusion" placeholder="Conclusion of generated paper" class="form-control" rows="10"></textarea>'
                    self.wfile.write(json.dumps({'message': "Papers selected", 'result': output}))
                    continue
                if item.name == "newinstitute":
                    newinstitute = item.value
                    continue
                if item.name == "newtitle":
                    newtitle = item.value
                    continue
                if item.name == "newauthors":
                    newauthors = item.value
                    continue
                if item.name == "newdate":
                    newdate = item.value
                    continue
                if item.name == "newabstract":
                    newabstract = item.value
                    continue
                if item.name == "newconclusion":
                    newconclusion = item.value
                    continue
                if item.name == "newinfo":
                    #self.wfile.write(json.dumps({'message': output, 'result': ""}))
                    continue
                if item.name == "latextemplatecreate":
                    bibtexitems = {}
                    content = ""
                    for i, title in enumerate(cited_pdfs_title):
                        for j in selectedpapers:
                            #print int(i) is int(j)
                            if (j != '' and int(i) is int(j)):
                                bibtexitem = ("%s\n\n") % webactions.parseBibtex(title).encode()
                                bibtexref = webactions.parseBibtexRef(bibtexitem)
                                bibtexitems[bibtexref] = bibtexitem
                                content += "\section{%s}\n" % (webactions.escapelatex(title))
                                content += "%s\n\cite{%s}\n\n\n" % (webactions.escapelatex(webactions.parseAbstract(title)), bibtexref)

                    for i, title in enumerate(cited_cited_pdfs_title):
                        for j in selectedsubpapers:
                            #print int(i) is int(j)
                            if (j != '' and int(i) is int(j)):
                                bibtexitem = ("%s\n\n") % webactions.parseBibtex(title).encode()
                                bibtexref = webactions.parseBibtexRef(bibtexitem)
                                bibtexitems[bibtexref] = bibtexitem
                                content += "\section{%s}\n" % (webactions.escapelatex(title))
                                content += "%s\n\cite{%s}\n\n\n" % (webactions.escapelatex(webactions.parseAbstract(title)), bibtexref)

                    content += "\section{Conclusion}\n%s\n\n\n" % (webactions.escapelatex(newconclusion))

                    latextemplate = webactions.getlatex(webactions.escapelatex(newtitle), webactions.escapelatex(newabstract), webactions.escapelatex(newauthors), webactions.escapelatex(newinstitute), webactions.escapelatex(newdate), content).encode()
                    bibtextemplate = "\n\n\n".join('%s' % (bibtexitems[k]) for k in bibtexitems)
                    output = ""
                    output += '<textarea id="latextemplate" name="latextemplate" class="form-control" rows="20">%s</textarea>' % latextemplate
                    output += '<textarea id="bibtextemplate" name="bibtextemplate" class="form-control" rows="10">%s</textarea>' % bibtextemplate

                    self.wfile.write(json.dumps({'message': "New info parsed to LaTeX" + output, 'result': ""}))
                    continue
                if item.name == "latextemplate":
                    latextemplate = item.value
                    output = ""
                    output += '<textarea id="latextemplate" name="latextemplate" class="form-control" rows="20">%s</textarea>' % latextemplate
                    output += '<textarea id="bibtextemplate" name="bibtextemplate" class="form-control" rows="10">%s</textarea>' % bibtextemplate
                    webactions.pdflatex(latextemplate, bibtextemplate)
                    self.wfile.write(json.dumps({'message': output, 'result': ""}))
                    continue

    def do_GET(self):
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


class MyTCPServer(SocketServer.TCPServer):
    allow_reuse_address = True


httpd = MyTCPServer(("", 8000), CustomHandler)

print "serving at port", 8000
httpd.serve_forever()
