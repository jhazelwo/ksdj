from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

from cfgksdj import LOCAL_ADMIN_URL

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='core/index.html'), name='home'),
    #
    url(r'^client/', include('client.urls', namespace='client')),
    url(r'^vlan/',   include('vlan.urls', namespace='vlan')),
    url(r'^user/',   include('human.urls', namespace='human')),
    url(r'^recent/', include('recent.urls', namespace='recent')),
    #
    url(LOCAL_ADMIN_URL, include(admin.site.urls)),
)
