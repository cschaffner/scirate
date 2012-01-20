from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
import urllib
from xml.dom.minidom import parse
from rate.models import Article
from datetime import date
from django.views.generic import DetailView, ListView


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

def articles(request,year=date.today().year,month='all',day='all'):
    queryset=Article.objects.filter(date__year=year)
    if month<>'all':
        queryset=queryset.filter(date__month=month)
    if day<>'all':
        queryset=queryset.filter(date__day=day)        
    if request.user.is_authenticated():
        # Do something for authenticated users.
        queryset = list(queryset)
        queryset.sort(key = lambda x:-x.score())
        return render_to_response('index.html', {"article_list": queryset, 
                                                 "year": year, "month": month, "day": day})
    else:
        # Do something for anonymous users.
        return HttpResponse("Anonymous here")

def like(request, id):
    if request.user.is_authenticated():
        # Do something for authenticated users.
        art=Article.objects.get(identifier=id)
        art.dislikes.remove(request.user)          
        art.likes.add(request.user)
        return redirect('/rate')
    else:
        # Do something for anonymous users.
        return HttpResponse("You need to be logged in to like something")

def dislike(request, id):
    if request.user.is_authenticated():
        # Do something for authenticated users.
        art=Article.objects.get(identifier=id)
        art.likes.remove(request.user)          
        art.dislikes.add(request.user)
        art.save
        return redirect('/rate')
    else:
        # Do something for anonymous users.
        return HttpResponse("You need to be logged in to dislike something")
    
    
    
#ListView.as_view(
#        queryset=Article.objects.order_by('-date')[:50],
#        context_object_name='latest_article_list',
#        template_name='index.html')
    