# client/views.py

from django.views import generic
from django.contrib import messages
from django.shortcuts import redirect

from core import kickstart
from human.mixins import RequireStaffMixin
from recent.functions import log_form_valid

from vlan.models import VLAN

from .forms import ClientForm
from .models import Client


class Index(generic.ListView):
    """ List of existing kickstart clients """
    form_class, model = ClientForm, Client
    template_name = 'client/index.html'


class ClientDetailView(generic.DetailView):
    """ View details of a client """
    form_class, model = ClientForm, Client
    template_name = 'client/ClientDetailView.html'


class ClientCreateView(RequireStaffMixin, generic.CreateView):
    """ Add a client to kickstart """
    form_class, model = ClientForm, Client
    template_name = 'client/ClientCreateView.html'

    def get_context_data(self, **kwargs):
        """ """
        context = super(ClientCreateView, self).get_context_data(**kwargs)
        context['vlans'] = VLAN.objects.all()
        return context

    def form_valid(self, form):
        """ """ 
        if not kickstart.client_create(self, form):
            return super(ClientCreateView, self).form_invalid(form)
        messages.success(self.request, 'Client added to kickstart!')
        log_form_valid(self, form)
        return super(ClientCreateView, self).form_valid(form)


class ClientUpdateView(RequireStaffMixin, generic.UpdateView):
    """ Edit a kickstart client """
    form_class, model = ClientForm, Client
    template_name = 'client/ClientUpdateView.html'

    def get_context_data(self, **kwargs):
        """ """
        context = super(ClientUpdateView, self).get_context_data(**kwargs)
        context['vlans'] = VLAN.objects.all()
        return context

    def form_valid(self, form):
        """ """
        old = Client.objects.get(id=self.object.id)
        if not kickstart.client_delete(self, old):
            return super(ClientUpdateView, self).form_invalid(form)
        if not kickstart.client_create(self, form):
            return super(ClientUpdateView, self).form_invalid(form)
        messages.success(self.request, 'Changes saved!')
        log_form_valid(self, form)
        return super(ClientUpdateView, self).form_valid(form)
