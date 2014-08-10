# client/urls.py
from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ksdj.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    #
    #url(r'^client/', include('client.urls'), namespace='client')
    url(r'^add/$', views.ClientCreateView.as_view(), name='create'),
)
