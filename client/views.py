# client/views.py

from django.views import generic
from django.contrib import messages

from core import kickstart

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

    def get_context_data(self, **kwargs):
        context = super(ClientCreateView, self).get_context_data(**kwargs)
        context['vlans'] = VLAN.objects.all()
        return context

    def form_valid(self, form):
        if not kickstart.client_create(self, form):
            return super(ClientCreateView, self).form_invalid(form)
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
