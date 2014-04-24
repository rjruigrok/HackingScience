#!/usr/bin/env python

import mechanize
import urllib
import urllib2
import urlparse
import os
import uuid
from pyquery import PyQuery
import commands
import simplejson
import socket
import re
import tempfile
import shutil
from pymarkov import markov
from random import randrange


def downloadPDF(link):
    try:
        if link.find(".pdf") > 0:
            filename = "papers/"+str(uuid.uuid4())+".pdf"
            outputfile = open(filename, 'wb')
            try:
                urlopen = urllib2.urlopen(link)
                outputfile.write(urlopen.read())
                return filename
            except urllib2.HTTPError, e:
                return "HTTP Error: %d: %s : %s" % (e.code, e.msg, link)
            except urllib2.URLError, e:
                return "URL invalid: %s" % (link)
            outputfile.close()

        return "Pdf not found in url %s" % link
    except (socket.timeout) as err:
        return "Connection error while downloading pdf %s" % err


def parseTitle(localpdf):
    title = commands.getoutput('./pdftitle.py %s' % localpdf)
    return title


def parseAbstract(papertitle):
    try:
        lookupurl = "http://ieeexplore.ieee.org/search/searchresult.jsp?" + urllib.urlencode({'queryText': papertitle})
        page = urllib2.urlopen(lookupurl, "", 10)
        html = page.read()
        pq = PyQuery(html)
        abstract = pq('#abstract-1:first').text().encode('ascii', 'ignore')
        abstract = abstract.replace("View full abstract", "")
        return abstract
    except (socket.timeout) as err:
        return "Connection error while parsing abstract %s" % err


def parseKeywords(papertitle):
    results = []
    try:
        lookupurl = "http://ieeexplore.ieee.org/search/searchresult.jsp?" + urllib.urlencode({'queryText': papertitle})
        print lookupurl
        # browse their links
        mech = mechanize.Browser()
        mech.set_handle_robots(False)
        mech.open(lookupurl, timeout=5.0)

        links = mech.links()

        # check each link for containing pdf file
        for l in links:
            # fix abslute / relative paths
            path = urlparse.urljoin(l.base_url, l.url)
            if path.find("/xpl/articleDetails.jsp?tp=&arnumber=") > 0:
                try:
                    lookupurl = path.replace("articleDetails.jsp", "abstractKeywords.jsp")
                    print lookupurl
                    page = urllib2.urlopen(lookupurl, "", 10)
                    html = page.read()
                    pq = PyQuery(html)
                    keywordlinks = pq('.art-keywords li a')
                    for link in keywordlinks:
                        keyword = link.attrib['data-keyword']
                        if isinstance(keyword, str) and len(keyword) > 0:
                            results.append(keyword)
                    return results
                except urllib2.HTTPError, e:
                    print ("ERROR: %d: %s" % (e.code, e.msg))
                except urllib2.URLError, e:
                    print ("ERROR: %d: %s" % (0, "URL Error"))
                print papertitle + " > " + path

    except (socket.timeout) as err:
        print "Connection error while parsing bibtex for link %s : %s" % lookupurl, err
    except urllib2.HTTPError, e:
        print ("ERROR: %d: %s" % (e.code, e.msg))
    except urllib2.URLError, e:
        print "URLError %s" % lookupurl


def parseBibtex(papertitle):
    try:
        lookupurl = "http://dblp.kbs.uni-hannover.de/dblp/Search.action?" + urllib.urlencode({'q': papertitle})
        page = urllib2.urlopen(lookupurl, "", 10)
        html = page.read()
        start = "clip.setText('"
        end = "'); else"
        bibtex = html[html.find(start)+len(start):html.find(end)]
        bibtex = bibtex.replace(",###", ",\n    ")
        bibtex = bibtex.replace("###", " ")
        bibtex = bibtex.replace("crossref", "xcrossref")
        bibidentifier = bibtex[bibtex.find("{")+len("{"):bibtex.find(",")]
        if (len(bibidentifier) > 1):
            #bibtex = bibtex.replace(bibidentifier,)
            return bibtex
        return "No bibtex found"
    except (socket.timeout) as err:
        return "Connection error while parsing bibtex : %s" % err


def parseBibtexRef(bibtex):
    if bibtex is '':
        return ''
    firstsplit = bibtex.split("{")[1]
    return firstsplit.split(",")[0]


def parseCitations(papertitle):
    results = []
    try:
        lookupurl = "http://ieeexplore.ieee.org/search/searchresult.jsp?" + urllib.urlencode({'queryText': papertitle})
        print lookupurl
        # browse their links
        mech = mechanize.Browser()
        mech.set_handle_robots(False)
        mech.open(lookupurl, timeout=5.0)

        links = mech.links()

        # check each link for containing pdf file
        for l in links:
            # fix abslute / relative paths
            path = urlparse.urljoin(l.base_url, l.url)
            if path.find("/xpl/articleDetails.jsp?tp=&arnumber=") > 0:
                try:
                    lookupurl = path.replace("articleDetails.jsp", "abstractReferences.ajax")
                    page = urllib2.urlopen(lookupurl, "", 10)
                    html = page.read()
                    pq = PyQuery(html)
                    citations = pq('li')
                    for citation in citations:
                        citationtext = citation.text.encode('ascii', 'ignore')
                        citationtext = re.sub('\s+', ' ', citationtext).strip()
                        if len(citationtext) > 0:
                            results.append(citationtext)
                    return results
                except urllib2.HTTPError, e:
                    print ("ERROR: %d: %s" % (e.code, e.msg))
                except urllib2.URLError, e:
                    print ("ERROR: %d: %s" % (0, "URL Error"))
                print papertitle + " > " + path

    except (socket.timeout) as err:
        print "Connection error while parsing bibtex for link %s : %s" % lookupurl, err
    except urllib2.HTTPError, e:
        print ("ERROR: %d: %s" % (e.code, e.msg))
    except urllib2.URLError, e:
        print "URLError %s" % lookupurl


def downloadCites(source_citations):
    result = []
    for citation in source_citations:
        googlefirst = googleresult(citation + " filetype:pdf")
        if googlefirst:
            result.append(googlefirst['url'])
    return result


def googleresult(keywords):
    searchurl = 'https://ajax.googleapis.com/ajax/services/search/web?' + urllib.urlencode({'v': '1.0', 'q': keywords, 'userip': '127.0.0.1'})
    req = urllib2.Request(searchurl)
    req.add_header('Referer', 'http://www.robruigrok.nl/')
    searchresults = urllib2.urlopen(req, None, 10)
    result = simplejson.load(searchresults)
    return get_first(result['responseData']['results'])
    #return json.loads(page.read())['responseData']['results']


def get_first(iterable, default=None):
    if iterable:
        for item in iterable:
            return item
    return default


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


def getlatex(title, abstract, author, institute, date, content):
    current = os.getcwd()
    tempdir = tempfile.mkdtemp()
    shutil.copyfile(current + "/latextemplate/biblio.bib", tempdir + "/biblio.bib")
    shutil.copyfile(current + "/latextemplate/template.tex", tempdir + "/template.tex")
    return parsefile(tempdir + "/template.tex", title, abstract, author, institute, date, content)


def parsefile(texfile, title, abstract, author, institute, date, content):
    fr = open(texfile, 'r')
    lines = fr.read()
    lines = lines.replace("~TITLE~", title)
    lines = lines.replace("~AUTHOR~", author)
    lines = lines.replace("~EMAIL~", institute)
    lines = lines.replace("~ABSTRACT~", abstract)
    lines = lines.replace("~DATE~", date)
    lines = lines.replace("~INSTITUTE~", institute)

    keywordlist = markovtitle(abstract).split()
    keywordsused = []
    for keyword in keywordlist:
        if len(keyword) > 6:
            keywordsused.append(keyword)
    lines = lines.replace("~KEYWORDS~", ', '.join(keywordsused))
    lines = lines.replace("~PAPER~", content)
    return lines


def markovtitle(text):
    markov_dict = markov.train([text], 2)
    return markov.generate(markov_dict, randrange(4, 10), 2)


def pdflatex(latex, bibtex):
    pdflatexbin = "/usr/texbin/"
    current = os.getcwd()

    # Set up temporary working directory for latex
    tempdir = tempfile.mkdtemp()
    os.chdir(tempdir)

    fw = open(tempdir + "/template.tex", 'w')
    fw.write(latex)
    fw.close()

    fw = open(tempdir + "/biblio.bib", 'w')
    fw.write(bibtex)
    fw.close()

    # Build pdf file
    os.system(pdflatexbin + "pdflatex template.tex && " + pdflatexbin + "bibtex template && " + pdflatexbin + "pdflatex template.tex && " + pdflatexbin + "pdflatex template.tex && " + pdflatexbin + "pdflatex template.tex")
    # Copy result and cleanup temp
    if os.path.isfile(tempdir + "/template.pdf"):
        shutil.copyfile(tempdir + "/template.pdf", "%s/generated/result.pdf" % (current))
    shutil.rmtree(tempdir)
    os.chdir(current)


def escapelatex(latex):
    # List of characters that should be escaped in latex
    reservedchars = {
        '&':  r'\&',
        '%':  r'\%',
        '$':  r'\$',
        '#':  r'\#',
        '_':  r'\_',
        '{':  r'\{',
        '}':  r'\}',
        '~':  r'\~',
        '^':  r'\^',
        '\\': r'\\\\',
    }
    return "".join([reservedchars.get(char, char) for char in latex])
