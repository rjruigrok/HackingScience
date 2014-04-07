#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import tempfile
import shutil
from pymarkov import markov
from random import randrange
import time

def pdflatex(tempdir, current, number,title,abstract,content):
    pdflatexbin = "/usr/texbin/"

    # Set up temporary working directory for latex
    parsefile(tempdir + "/template.tex",title,abstract,content)
    os.chdir(tempdir)

    # Build pdf file
    os.system(pdflatexbin + "pdflatex template.tex && " + pdflatexbin + "bibtex template && " + pdflatexbin + "pdflatex template.tex && " + pdflatexbin + "pdflatex template.tex && " + pdflatexbin + "pdflatex template.tex")
    # Copy result and cleanup temp
    if os.path.isfile(tempdir + "/template.pdf"):
        shutil.copyfile(tempdir + "/template.pdf", "%s/generated/result_%03d.pdf" % (current, number))
    shutil.rmtree(tempdir)
    os.chdir(current)


def appendbib(bibfile, bibtex):
    fw = open(bibfile, 'a')
    fw.write(bibtex + "\n\n\n")
    fw.close()


#    fr.close()
#    os.remove(texfile)
#    fw = open(texfile, 'w')
#    fw.write(lines)
#    fw.close()


def markovtitle(text):
    markov_dict = markov.train([text], 2)
    return markov.generate(markov_dict, randrange(4,10), 2)


def getnextabstract(papers,tempdir):
    # select random paper (which is not already chosen)
    randomindex = randrange(0,len(papers))
    if randomindex in usedpapers:
        return getnextabstract(papers,tempdir)
    usedpapers.append(randomindex)

    print "abstract %d selected" % randomindex
    fn = papers[randomindex]

    # retrieve abstract
    abstractfile = "papers/" + fn.replace(".pdf",".abstract.txt")
    if os.path.isfile(abstractfile):
        fr = open(abstractfile, 'r')
        abstract = escapelatex(fr.read())
        if len(abstract) == 0:
            return getnextabstract(papers,tempdir)
        fr.close()
    else:
        return getnextabstract(papers,tempdir)

    # retrieve bibtex
    fr = open("papers/" + fn.replace(".pdf",".bib"), 'r')
    bibtex = fr.read()
    fr.close()
    if (len(bibtex) > 0):
        #bibtex = bibtex.replace("_","\_")
        appendbib(tempdir + "/biblio.bib",bibtex)
        abstract += "\cite{%s}" % fn
    return abstract
    #return getnextabstract(papers,tempdir)

def allpapertitles():
    titles = ""
    for fn in os.listdir("papers"):
        if (fn.endswith(".title.txt")):
            fr = open("papers/" + fn, 'r')
            title = fr.read()
            if not "No title found" in title and not "Could not convert PDF" in title:
                titles += " " + title
            fr.close()
            #print title
    return titles


# Put papers in a list
#papers = []
#for fn in os.listdir("papers"):
#    if fn.endswith(".pdf"):
#        papers.append(fn)

#papertitles = allpapertitles()
#exit()
# Generate 100 random papers
for x in range(0, 0):
    usedpapers = []
    current = os.getcwd()
    tempdir = tempfile.mkdtemp()
    shutil.copyfile(current + "/latextemplate/biblio.bib", tempdir + "/biblio.bib")
    shutil.copyfile(current + "/latextemplate/template.tex", tempdir + "/template.tex")

    # generate random sections...
    abstrandom = getnextabstract(papers,tempdir)
    papertitle = markovtitle(papertitles).capitalize()
    intro = getnextabstract(papers,tempdir)
    bgwork = getnextabstract(papers,tempdir)
    problemdesc = getnextabstract(papers,tempdir)
    propsol1 = getnextabstract(papers,tempdir)
    propsol2 = getnextabstract(papers,tempdir)
    random7 = getnextabstract(papers,tempdir)
    randomsect1 = getnextabstract(papers,tempdir)
    sectiontitle1 = markovtitle(randomsect1).capitalize()
    randomsect2 = getnextabstract(papers,tempdir)
    randomsect3 = getnextabstract(papers,tempdir)
    sectiontitle2 = markovtitle(randomsect3).capitalize()
    randomsect4 = getnextabstract(papers,tempdir)
    randomsect5 = getnextabstract(papers,tempdir)
    randomsect6 = getnextabstract(papers,tempdir)
    randomsect7 = getnextabstract(papers,tempdir)
    subsectiontitle1 = markovtitle(random7).capitalize()
    random8 = getnextabstract(papers,tempdir)
    subsectiontitle2 = markovtitle(random8).capitalize()
    concl = getnextabstract(papers,tempdir)
    future = getnextabstract(papers,tempdir)

    # Build PDF from tex
    pdflatex(tempdir, current, x,papertitle,
        abstrandom,
        "\section{Introduction} %s \section{Background work} %s \section{Problem description} %s \section{Proposed solution} %s %s \section{%s} %s %s %s \section{%s} %s %s %s %s \subsection{%s} %s \subsection{%s} %s \section{Conclusion} %s \section{Future work} %s " %
        (intro, bgwork, problemdesc, propsol1, propsol2, sectiontitle1, randomsect1, randomsect2, randomsect3, sectiontitle2, randomsect4, randomsect5, randomsect6, randomsect7, subsectiontitle1, random7, subsectiontitle2, random8, concl, future))

    #print tempdir
    #exit()
