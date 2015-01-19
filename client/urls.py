# client/urls.py
from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
    #
    url(r'^$',                              views.Index.as_view(),            name='index'),
    url(r'^(?P<pk>\d+)/delete/',            views.ClientDeleteView.as_view(), name='delete'),
    url(r'^(?P<pk>\d+)/update/kickstart/$', views.ClientCustomView.as_view(), name='kickstart'),
    url(r'^(?P<pk>\d+)/update/$',           views.ClientUpdateView.as_view(), name='update'),
    url(r'^(?P<pk>\d+)/$',                  views.ClientDetailView.as_view(), name='detail'),
    url(r'^add/$',                          views.ClientCreateView.as_view(), name='create'),
)
