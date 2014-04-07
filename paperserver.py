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

latextemplate = "empty"

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

        global latextemplate

        if self.path == "/action":
            for item in form.list:
                print "%s=%s" % (item.name, item.value)
                if item.name == "parsepapertitle":
                    source_title = item.value
                    print source_title
                    self.wfile.write(json.dumps({'message': "Title parsed from paper", 'result': source_title}))
                    continue
                if item.name == "parseabstract":
                    source_abstract = webactions.parseAbstract(source_title)
                    self.wfile.write(json.dumps({'message': "Abstract parsed from paper", 'result': source_abstract}))
                    continue
                if item.name == "parsebibtex":
                    source_bibtex = webactions.parseBibtex(source_title)
                    self.wfile.write(json.dumps({'message': "Bibtex parsed from paper", 'result': source_bibtex}))
                    continue
                if item.name == "parsecitations":
                    source_citations = webactions.parseCitations(source_title)
                    output = ""
                    for citation in source_citations:
                        output += citation + "\n"
                        cited_pdfs_citation.append(citation)
                        title = webactions.get_first(re.compile('".*?"', re.DOTALL).findall(citation))
                        if title is None:
                            continue
                        title = title.replace('"', '')
                        cited_pdfs_title.append(title)
                    self.wfile.write(json.dumps({'message': "Citations parsed from paper", 'result': output}))
                    continue
                if item.name == "parsecitationcites":
                    output = ""
                    for title in cited_pdfs_title:
                        try:
                            subcitations = webactions.parseCitations(title)
                            output += title + "\n"
                            for subcitation in subcitations:
                                cited_cited_pdfs_citation.append(subcitation)
                                title = webactions.get_first(re.compile('".*?"', re.DOTALL).findall(subcitation))
                                if title is None:
                                    continue
                                title = title.replace('"', '')
                                cited_cited_pdfs_title.append(title)
                                output += " - " + title + "\n"
                                #break
                            output += "\n"
                            break
                        except TypeError:
                            print "Can't parse citations for paper " + title
                    self.wfile.write(json.dumps({'message': "Citing citations parsed from paper", 'result': output}))

                    #for citedfile in cited_pdfs:
                    #    print "Parse cited file " + citedfile
                    #    parsedtitle = webactions.parseTitle(citedfile)
                    #    if "No such file" not in parsedtitle and "Could not convert PDF to XML" not in parsedtitle:
                    #        output += parsedtitle + "\n"
                    #        cited_pdfs_title.append(parsedtitle)
                    #        cited_citations = webactions.parseCitations(parsedtitle)
                    #        for citation in cited_citations:
                    #            output += " - " + citation + "\n"

                    #self.wfile.write(json.dumps({'message': "Titles parsed from cited papers", 'result': output}))
                    continue
                if item.name == "parsekeywords":

                    parse_keywords = webactions.parseKeywords(source_title)
                    if isinstance(parse_keywords, collections.Iterable):
                        for keyword in parse_keywords:
                            if keyword in parsedkeywords:
                                parsedkeywords[keyword] += 1
                            else:
                                parsedkeywords[keyword] = 1

                    for i, title in enumerate(cited_pdfs_title):
                        parse_keywords = webactions.parseKeywords(title)
                        if isinstance(parse_keywords, collections.Iterable):
                            for keyword in parse_keywords:
                                if keyword in parsedkeywords:
                                    parsedkeywords[keyword] += 1
                                else:
                                    parsedkeywords[keyword] = 1
                            #break
                    for i, title in enumerate(cited_cited_pdfs_title):
                        parse_keywords = webactions.parseKeywords(title)
                        if isinstance(parse_keywords, collections.Iterable):
                            for keyword in parse_keywords:
                                if keyword in parsedkeywords:
                                    parsedkeywords[keyword] += 1
                                else:
                                    parsedkeywords[keyword] = 1

                    output = ""
                    for key in parsedkeywords:
                        output += "%d : %s\n" % (parsedkeywords[key], key)
                    self.wfile.write(json.dumps({'message': "Keywords searched and downloaded from original and cited papers", 'result': output}))
                    continue
                if item.name == "downloadcitationcites":
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
                    #self.wfile.write(json.dumps({'message': "Not implemented", 'result': ""}))
                    continue
                if item.name == "selectsubpapers":
                    selectedsubpapers = item.value.split(",")
                    self.wfile.write(json.dumps({'message': "Papers selected", 'result': ", ".join(selectedpapers) + ", ".join(selectedsubpapers)}))
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
                if item.name == "titleauthors":
                    output = ""
                    output += '<textarea id="newabstract" name="newabstract" class="form-control" rows="10">%s</textarea>' % source_abstract
                    self.wfile.write(json.dumps({'message': "Updated title and authors<br />" + output, 'result': newtitle + "\n" + newinstitute + "\n" + newdate + "\n" + newauthors}))
                    continue
                if item.name == "newabstract":
                    newabstract = item.value
                    content = ""
                    for i, title in enumerate(cited_pdfs_title):
                        if i in selectedpapers:
                            content += webactions.escapelatex(title) + "\n"
                            content += webactions.escapelatex(webactions.parseAbstract(title)) + "\n\n\n"
                    for i, title in enumerate(cited_cited_pdfs_title):
                        if i in selectedsubpapers:
                            content += webactions.escapelatex(title) + "\n"
                            content += webactions.escapelatex(webactions.parseAbstract(title)) + "\n\n\n"

                    latextemplate = webactions.getlatex(webactions.escapelatex(newtitle), webactions.escapelatex(newabstract), webactions.escapelatex(newauthors), webactions.escapelatex(newinstitute), webactions.escapelatex(newdate), content)
                    output = ""
                    output += '<textarea id="latextemplate" name="latextemplate" class="form-control" rows="30">%s</textarea>' % latextemplate

                    self.wfile.write(json.dumps({'message': "Abstract entered <br />" + output, 'result': newabstract}))
                    continue
                if item.name == "latextemplate":
                    latextemplate = item.value

                    content = ""
                    print "test"
                    for i, title in enumerate(cited_pdfs_title):
                        print i
                        if i in selectedpapers:
                            content += webactions.escapelatex(title) + "\n"
                            content += webactions.escapelatex(webactions.parseAbstract(title)) + "\n\n\n"
                    for i, title in enumerate(cited_cited_pdfs_title):
                        if i in selectedsubpapers:
                            content += webactions.escapelatex(title) + "\n"
                            content += webactions.escapelatex(webactions.parseAbstract(title)) + "\n\n\n"

                    output = ""
                    output += '<textarea id="latextemplate" name="latextemplate" class="form-control" rows="30">%s</textarea>' % latextemplate
                    webactions.pdflatex(latextemplate, "")
                    self.wfile.write(json.dumps({'message': '<a href="/generated/result.pdf" title="" class="btn btn-success" target="_blank">Download PDF</a>' + output, 'result': ""}))
                    continue

    def do_GET(self):
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


class MyTCPServer(SocketServer.TCPServer):
    allow_reuse_address = True


httpd = MyTCPServer(("", 8000), CustomHandler)

print "serving at port", 8000
httpd.serve_forever()
