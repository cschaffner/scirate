from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView
from rate.models import Article
from datetime import date
from django.contrib.auth import views

#urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^mysite/', include('mysite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #    url(r'^admin/', include(admin.site.urls)),

urlpatterns = patterns('rate.views',
    url(r'^$', 'articles',{'year': date.today().year, 'month': date.today().month, 'day': date.today().day}),
    url(r'^(\d{4})/$', 'articles'),
    url(r'^(\d{4})/(\d{1,2})/$', 'articles'),
    url(r'^(\d{4})/(\d{1,2})/(\d+)/$', 'articles'),
    url(r'^detail/(?P<pk>\d{4}\.\d{4})/$',
        DetailView.as_view(
            model=Article,
            template_name='detail.html')),
    url(r'^like/(?P<id>\d{4}\.\d{4})/$', 'like'),
    url(r'^dislike/(?P<id>\d{4}\.\d{4})/$', 'dislike'),
    url(r'^vote/', 'vote'),
    url(r'^accounts/logout/$', 'logout_view'),            
)
urlpatterns += patterns('',
#    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^accounts/',  include('registration.backends.default.urls')),
)
