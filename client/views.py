# client/views.py

from django.views import generic
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy

from core import kickstart
from human.mixins import RequireStaffMixin
from recent.functions import log_form_valid

from vlan.models import VLAN

from .forms import ClientForm, CustomForm
from .models import Client


class Index(generic.ListView):
    """ List of existing kickstart clients """
    form_class, model = ClientForm, Client
    template_name = 'client/index.html'


class ClientDetailView(generic.DetailView):
    """ View details of a client """
    form_class, model = ClientForm, Client
    template_name = 'client/ClientDetailView.html'


class ClientCustomView(RequireStaffMixin, generic.UpdateView):
    """ Edit the kickstart config file for a client """
    form_class, model = CustomForm, Client
    template_name = 'client/ClientCustomView.html'
    

    def form_valid(self, form):
        """ """
        if not kickstart.update_kickstart_file(self, form):
            return super(ClientCustomView, self).form_invalid(form)
        messages.success(self.request, 'Changes saved!')
        log_form_valid(self, form)
        return super(ClientCustomView, self).form_valid(form)


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
        self.old = Client.objects.get(id=self.object.id)
        if not kickstart.client_delete(self):
            return super(ClientUpdateView, self).form_invalid(form)
        if not kickstart.client_create(self, form):
            return super(ClientUpdateView, self).form_invalid(form)
        messages.success(self.request, 'Changes saved!')
        log_form_valid(self, form)
        return super(ClientUpdateView, self).form_valid(form)


class ClientDeleteView(generic.DeleteView):
    """ Delete a client """
    form_class, model = ClientForm, Client
    template_name = 'client/ClientDeleteView.html'
    success_url = reverse_lazy('client:index')

    def delete(self, request, *args, **kwargs):
        self.old = self.get_object()
        if not kickstart.client_delete(self):
            return super(ClientDeleteView, self).get(request, *args, **kwargs)
        messages.success(self.request, 'Client {0} removed!'.format(self.old.name))
        return super(ClientDeleteView, self).delete(request, *args, **kwargs)
