from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView
from rate.models import Article
from django.contrib.auth.models import User

from datetime import date
from django.contrib.auth import views


urlpatterns = patterns('rate.views',
    # those are all handled by the articles-view
    # paranthesis in the regular expressions indicate arguments that will be passed to the view
    # in the same order (year, month, date)
    url(r'^$', 'articles',{'year': date.today().year, 'month': date.today().month, 'day': date.today().day}),
    url(r'^(\d{4})/$', 'articles'),
    url(r'^(\d{4})/(\d{1,2})/$', 'articles'),
    url(r'^(\d{4})/(\d{1,2})/(\d+)/$', 'articles'),
    # shortcut to a detail view of an article, avoiding an extra detail-view
    url(r'^detail/(?P<pk>\d{4}\.\d{4})/$',
        DetailView.as_view(
            model=Article,
            template_name='detail.html')),
    # called by AJAX in order to vote for an article
    url(r'^vote/', 'vote'),
    # show user information
    url(r'^user/', 'user'), 
    # call the rate-specific logout-view instead of the standard logout-view
    url(r'^accounts/logout/$', 'logout_view'),            
)
urlpatterns += patterns('',
    # standard registration business
    url(r'^accounts/',  include('registration.backends.default.urls')),
)
