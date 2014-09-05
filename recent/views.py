# recent/views.py

from django.views import generic
from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from . import models

class Index(generic.ListView):
    model = models.Log
    template_name = 'recent/index.html'

