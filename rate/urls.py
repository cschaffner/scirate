from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView
from rate.models import Article

#urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^mysite/', include('mysite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #    url(r'^admin/', include(admin.site.urls)),

urlpatterns = patterns('',
    url(r'^$',
        ListView.as_view(
            queryset=Article.objects.order_by('-date')[:5],
            context_object_name='latest_article_list',
            template_name='scirate/index.html')),
    url(r'^(?P<pk>\d+)/$',
        DetailView.as_view(
            model=Article,
            template_name='scirate/detail.html')),
    url(r'^loadtoday/$', 'scirate.views.loadtoday'),            
    # url(r'^(?P<pk>\d+)/results/$',
    #     DetailView.as_view(
    #         model=Poll,
    #         template_name='scirate/results.html'),
    #     name='poll_results'),
    # url(r'^(?P<poll_id>\d+)/vote/$', 'scirate.views.vote'),
)
