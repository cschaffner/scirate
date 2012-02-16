from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from rate.models import Article, DownloadAction
from datetime import date, datetime, timedelta
from django.views.generic import DetailView, ListView
from django.contrib.auth import logout
from django.utils import simplejson
from django.contrib.auth.decorators import login_required

import logging

@login_required
def user(request):
    # Get an instance of a logger
    logger = logging.getLogger('scirate.rate')
    logger.debug(request.user.username)    
    
    # display user data (only makes sense, if user is logged in)
    return render_to_response('user.html', {'user': request.user})

    
def articles(request,year=date.today().year,month='all',day='all'):
    # first check for new articles on the arxiv
    Article.objects.update()
    # create query of all year's articles sorted by decreasing score
    # due to lazy querying by Django, this should not be inefficient
    # all those articles are only retrieved when actually needed
    queryset=Article.objects.filter(date__year=year).order_by('-score')
    # further refine the query by month and day (if applicable)
    if month<>'all':
        queryset=queryset.filter(date__month=month)
    if day<>'all':
        queryset=queryset.filter(date__day=day) 
    # convert the queryset into a list (possibly inefficient)
    # this is a workaround, because I do not know how to sort a queryset
    # according to the complicated score-function below, without using custom SQL code
    queryset = list(queryset)
    queryset.sort(key = lambda x:(-x.score*1000 - x.abstract_expansions.count() - x.anonymous_abs_exp))
    
    # TODO: having both user and request looks redundant...
    return render_to_response('articles.html', {"article_list": queryset, 
        "year": year, "month": month, "day": day,
        "user": request.user, "request": request})

def vote(request):
    result = {'success':False}
    # Get an instance of a logger
    logger = logging.getLogger('scirate.rate')
    
    if request.user.is_authenticated():

# [don't remember why I commented that out, is_ajax() property should probably be checked here]
#        if (request.method == u'GET' and request.is_ajax()):
        if (request.method == u'GET'):
            GET = request.GET
            logger.info(GET)
            if GET.has_key(u'identifier') and GET.has_key(u'vote'):
                ident = GET[u'identifier']
                vote = GET[u'vote']
                # retrieve article, TODO: what if this article does not exist?
                art=Article.objects.get(identifier=ident)
                if vote == u"like":
                    # remove possible dislikes
                    art.dislikes.remove(request.user)
                    if art.likes.filter(username=request.user.username):
                        #   If this user already likes the article, then the like should be removed
                        art.likes.remove(request.user)
                    else:
                        #   add the user to the list of likes      
                        art.likes.add(request.user)
                elif vote == u"dislike":
                    # remove a possible like by this user
                    art.likes.remove(request.user)  
                    if art.dislikes.filer(username=request.user.username):
                        #   If this user already dislikes the article, then the dislike should be removed
                        art.dislikes.remove(request.user)
                    else:
                        #   add the user to the list of dislikes    
                        art.dislikes.add(request.user)                        
                elif vote == u"abstract":
                    # add user to the abstract_expansion list of the article
                    art.abstract_expansions.add(request.user)
                # for the many-to-many relation changes above, it is not necessary to call the 
                # the .save() method 
                # now is the moment to update the score of the article                
                art.updatescore()
                # TODO: inform the javascript if like/dislike has been removed
                result={'success':True, 'score':art.score}
                logger.debug(result)
    else:
        # register anonymous abstract expansion
        # TODO: avoid that the same anonymous user can arbitrarily increase this counter
        #       maybe the anonymous user is not that anonymous after all ?
        #       check what kind of things (like IP-address) one could retrieve from the 
        #       django request.user object to make anonymous unique
        #       we might then have to keep track of those IP-addresses...
        if (request.method == u'GET' and request.is_ajax()):
            GET = request.GET
            logger.info(GET)
            if GET.has_key(u'identifier') and GET.has_key(u'vote'):
                ident = GET[u'identifier']
                vote = GET[u'vote']
                if vote == u"abstract":
                    # retrieve article, TODO: what if this article does not exist?
                    art=Article.objects.get(identifier=ident)
                    art.anonymous_abs_exp += 1
                    art.save()
                    logger.info('increased anonymous abstract expansion to {0}'.format(art.anonymous_abs_exp))
                    result={'success':True, 'score':art.score}
                elif (vote == u"like" or vote == u"dislike"):
                    result={'success':False, 'reason':'not logged in'}
        
        # TODO: javascript should display a message that one has to login in order to vote
        #       return appropriate response

    # convert result from Python dictionary to proper JSON
    json = simplejson.dumps(result)
    return HttpResponse(json, mimetype='application/json')  
   
def logout_view(request):
    # logout current user
    logout(request)
    # redirect to today's articles
    return redirect('/rate')
    