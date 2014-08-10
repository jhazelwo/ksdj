# client/views.py
from __future__ import absolute_import

from django.views import generic
from django.contrib import messages

from vlan.models import VLAN

from .forms import ClientForm
from .models import Client


class Index(generic.TemplateView):
    """ default /client/ view """
    form_class, model = ClientForm, Client
    template_name = 'client/index.html'


class ClientCreateView(generic.CreateView):
    """ """
    form_class, model = ClientForm, Client
    template_name = 'client/ClientCreateView.html'

    def form_valid(self, form):
        messages.success(self.request, 'Client added to kickstart!')
        return super(ClientCreateView, self).form_valid(form)


class ClientDetailView(generic.DetailView):
    """ """
    form_class, model = ClientForm, Client
    template_name = 'client/ClientDetailView.html'


class ClientUpdateView(generic.UpdateView):
    """ """
    form_class, model = ClientForm, Client
    template_name = 'client/ClientUpdateView.html'
