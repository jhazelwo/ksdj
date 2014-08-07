from django.conf.urls import patterns, include, url
from django.contrib import admin

from core.views import Index

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ksdj.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$',  Index.as_view(), name='home'),
)
