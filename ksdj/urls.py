from django.conf.urls import patterns, include, url
from django.contrib import admin

from core import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ksdj.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    #
    url(r'^$',        views.Index.as_view(), name='home'),
    url(r'^login$',   views.LoginFormView.as_view(), name='login'),
    url(r'^logout$',  views.LogoutFormView.as_view(), name='logout'),
)
