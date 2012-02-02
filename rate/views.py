from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from rate.models import Article, DownloadAction
from datetime import date, datetime, timedelta
from django.views.generic import DetailView, ListView
from django.contrib.auth import logout
from django.utils import simplejson

import logging

def articles(request,year=date.today().year,month='all',day='all'):
    # check for new articles on the arxiv
    Article.objects.update()
    queryset=Article.objects.filter(date__year=year).order_by('-score')
    if month<>'all':
        queryset=queryset.filter(date__month=month)
    if day<>'all':
        queryset=queryset.filter(date__day=day) 
    queryset = list(queryset)
    queryset.sort(key = lambda x:(-x.score*1000 - x.abstract_expansions.count() - x.anonymous_abs_exp))
       
    return render_to_response('articles.html', {"article_list": queryset, 
        "year": year, "month": month, "day": day,
        "user": request.user, "request": request})

def vote(request):
    if request.user.is_authenticated():
        # Get an instance of a logger
        logger = logging.getLogger('scirate.rate')

        result = {'success':False}
#        if (request.method == u'GET' and request.is_ajax()):
        if (request.method == u'GET'):
            GET = request.GET
            logger.info(GET)
            if GET.has_key(u'identifier') and GET.has_key(u'vote'):
                ident = GET[u'identifier']
                vote = GET[u'vote']
                art=Article.objects.get(identifier=ident)
                if vote == u"like":
                    art.dislikes.remove(request.user)          
                    art.likes.add(request.user)
                elif vote == u"dislike":
                    art.likes.remove(request.user)          
                    art.dislikes.add(request.user) 
                elif vote == u"abstract":
                    art.abstract_expansions.add(request.user)                 
                art.updatescore()
                result={'success':True, 'score':art.score}
                logger.info(result)
        json = simplejson.dumps(result)
        return HttpResponse(json, mimetype='application/json')  
    else:
        # Do something for anonymous users.
        return HttpResponse("You need to be logged in to like something")

def like(request, id):
    if request.user.is_authenticated():
        results = {'success':False}
        if request.method == "POST":  
            ident = request.POST['identifier']
            art=Article.objects.get(identifier=ident)
            art.dislikes.remove(request.user)          
            art.likes.add(request.user)
        if request.is_ajax():  
            results = {'success':True}
        json = simplejson.dumps(results)
        return HttpResponse(json, mimetype='application/json')  
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

def logout_view(request):
    logout(request)
    return redirect('/rate')

    
#ListView.as_view(
#        queryset=Article.objects.order_by('-date')[:50],
#        context_object_name='latest_article_list',
#        template_name='index.html')
    