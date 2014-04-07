#!/usr/bin/env python

import mechanize
import urllib2
import urlparse
import os
from itertools import count


# set some websites containing links to pdf files
urls = []
urls.append("http://www.cs.huji.ac.il/labs/danss/p2p/resources.html")
urls.append("http://freehaven.net/anonbib/date.html")

# set target location on disk
filenameiter = ("papers/paper_%04i.pdf" % i for i in count(1))
if not os.path.exists('papers'):
        os.makedirs('papers')

# and download all pdf files for every website
for url in urls:
    try:
        # browse their links
        mech = mechanize.Browser()
        mech.set_handle_robots(False)
        mech.open(url, timeout=5.0)
    except urllib2.HTTPError, e:
        print ("ERROR: %d: %s : %s" % (e.code, e.msg, url))

    links = mech.links()

    # check each link for containing pdf file
    for l in links:
        # fix abslute / relative paths
        path = urlparse.urljoin(l.base_url, l.url)
        if path.find(".pdf") > 0:
            filename = next(filenameiter)
            outputfile = open(filename, 'wb')
            try:
                urlopen = urllib2.urlopen(path)
                outputfile.write(urlopen.read())
            except urllib2.HTTPError, e:
                print ("ERROR: %d: %s : %s" % (e.code, e.msg, url))
            except urllib2.URLError, e:
                print ("ERROR: %d: %s : %s" % (0, "URL Error", url))
            outputfile.close()
            print filename + " > " + path
