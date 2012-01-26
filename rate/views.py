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
    queryset=Article.objects.filter(date__year=year)
    if month<>'all':
        queryset=queryset.filter(date__month=month)
    if day<>'all':
        queryset=queryset.filter(date__day=day) 
        tomorrow=date(int(year),int(month),int(day))+timedelta(days=1)
        yesterday=date(int(year),int(month),int(day))-timedelta(days=1)
    queryset = list(queryset)
    queryset.sort(key = lambda x:-x.score())
    
    
    if request.user.is_authenticated():
        # Do something for authenticated users.
        return render_to_response('index_auth.html', {"article_list": queryset, 
            "year": year, "month": month, "day": day,
            "tom_year": tomorrow.year, "tom_month": '%02d' % tomorrow.month, "tom_day": '%02d' % tomorrow.day,
            "yes_year": yesterday.year, "yes_month": '%02d' % yesterday.month, "yes_day": '%02d' % yesterday.day,            
            "user": request.user})
    else:
        # Do something for anonymous users.
        return render_to_response('index.html', {"article_list": queryset, 
                                                 "year": year, "month": month, "day": day})

def vote(request):
    if request.user.is_authenticated():
        # Get an instance of a logger
        logger = logging.getLogger('scirate.rate')

        results = {'success':False}
        if (request.method == u'GET' and request.is_ajax()):
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
                result={'success':True, 'score':art.likes.count() - art.dislikes.count()}
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
    