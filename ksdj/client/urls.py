# client/urls.py
from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
                       url(r'^$',                              views.Index.as_view(),  name='index'),
                       url(r'^(?P<pk>\d+)/delete/',            views.Delete.as_view(), name='delete'),
                       url(r'^(?P<pk>\d+)/update/kickstart/$', views.Custom.as_view(), name='kickstart'),
                       url(r'^(?P<pk>\d+)/update/$',           views.Update.as_view(), name='update'),
                       url(r'^(?P<pk>\d+)/$',                  views.Detail.as_view(), name='detail'),
                       url(r'^add/$',                          views.Create.as_view(), name='create'),
                       )
