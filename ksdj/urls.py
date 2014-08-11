from django.conf.urls import patterns, include, url
from django.contrib import admin

from core import views

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    #
    url(r'^$',        views.Index.as_view(), name='home'),
    url(r'^login$',   views.LoginFormView.as_view(), name='login'),
    url(r'^logout$',  views.LogoutFormView.as_view(), name='logout'),
    #
    url(r'^client/', include('client.urls', namespace='client')),
    url(r'^vlan/',   include('vlan.urls', namespace='vlan')),
)
