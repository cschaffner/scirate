from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
import urllib
from xml.dom.minidom import parse
from rate.models import Article
from datetime import *


def loadtoday(request):
    URL = "http://export.arxiv.org/oai2?verb=ListRecords&set=physics:quant-ph&from=2012-01-12&metadataPrefix=arXivRaw"

    #    dom = parse(urllib.urlopen(URL))
    dom = parse('biglist.xml')

    articles = dom.getElementsByTagName('record')
    
    for node in articles:
        art = Article()
        nodedata = node.childNodes.item(3).childNodes.item(1)
        art.identifier = nodedata.getElementsByTagName('id').item(0).childNodes.item(0).nodeValue
        art.title = nodedata.getElementsByTagName('title').item(0).childNodes.item(0).nodeValue
        art.authors = nodedata.getElementsByTagName('authors').item(0).childNodes.item(0).nodeValue
        art.abstract = nodedata.getElementsByTagName('abstract').item(0).childNodes.item(0).nodeValue
        if nodedata.getElementsByTagName('journal-ref').length==1:
            art.journal_ref = nodedata.getElementsByTagName('journal-ref').item(0).childNodes.item(0).nodeValue
        if nodedata.getElementsByTagName('comments').length==1:
            art.arxiv_comments = nodedata.getElementsByTagName('comments').item(0).childNodes.item(0).nodeValue
        # determine date from first available version
        datestring = nodedata.getElementsByTagName('version').item(0).childNodes.item(0).childNodes.item(0).nodeValue
        date = datetime.strptime(datestring,'%a, %d %b %Y %H:%M:%S GMT')
        art.date = date.date()
        art.anonymous_abs_exp = 0
        art.save()
        
    # load today's articles here
    return HttpResponse("Added %s to load today's articles." % articles.length)

