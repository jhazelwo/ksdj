# vlan/urls.py
from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
    url(r'^add/$', views.VLANCreateView.as_view(), name='create'),
)
