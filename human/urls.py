# human/urls.py
from django.conf.urls import patterns, include, url
from . import views

urlpatterns = patterns('',
    #
    url(r'^$',          views.Index.as_view(),       name='index'),
    url(r'^logout/$',   views.LogoutView.as_view(),  name='logout'),
    url(r'^login/$',    views.LoginView.as_view(),   name='login'),
    url(r'^signup/$',   views.SignupView.as_view(),  name='create'),
)
