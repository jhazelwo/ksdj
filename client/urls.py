# client/urls.py
from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
    url(r'^add/$', views.ClientCreateView.as_view(), name='create'),
)
