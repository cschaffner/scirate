from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView
from rate.models import Article
from datetime import date

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
    url(r'^(\d{4})/(\d{2})/$', 'articles'),
    url(r'^(\d{4})/(\d{2})/(\d+)/$', 'articles'),
    url(r'^detail/(?P<pk>\d{4}\.\d{4})/$',
        DetailView.as_view(
            model=Article,
            template_name='detail.html')),
    url(r'^like/(?P<id>\d{4}\.\d{4})/$', 'like'),
    url(r'^dislike/(?P<id>\d{4}\.\d{4})/$', 'dislike'),
    url(r'^loadtoday/$', 'loadtoday'),            
    # url(r'^(?P<pk>\d+)/results/$',
    #     DetailView.as_view(
    #         model=Poll,
    #         template_name='results.html'),
    #     name='poll_results'),
    # url(r'^(?P<poll_id>\d+)/vote/$', 'scirate.views.vote'),
)
