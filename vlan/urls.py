# vlan/urls.py

from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
                       url(r'^$',                    views.Index.as_view(),          name='index'),
                       url(r'^(?P<pk>\d+)/delete/$', views.VLANDeleteView.as_view(), name='delete'),
                       url(r'^(?P<pk>\d+)/update/$', views.VLANUpdateView.as_view(), name='update'),
                       url(r'^(?P<pk>\d+)/$',        views.VLANDetailView.as_view(), name='detail'),
                       url(r'^add/$',                views.VLANCreateView.as_view(), name='create'),
                       )
