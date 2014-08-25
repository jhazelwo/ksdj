# client/views.py

from django.views import generic
from django.contrib import messages
from django.shortcuts import redirect

from core import kickstart
from human import authtools
from human.mixins import RequireStaffMixin

from vlan.models import VLAN

from .forms import ClientForm
from .models import Client


class Index(generic.ListView):
    """ default /client/ view """
    form_class, model = ClientForm, Client
    template_name = 'client/index.html'


class ClientCreateView(generic.CreateView):
    """ """
    form_class, model = ClientForm, Client
    template_name = 'client/ClientCreateView.html'

    def get(self, request, *args, **kwargs):
        if authtools.no_user(self):
            return redirect('{}?next={}'.format(reverse('human:login'),request.path))
        return super(ClientCreateView, self).get(request, *args, **kwargs)

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
        return super(ClientCreateView, self).form_valid(form)


class ClientDetailView(generic.DetailView):
    """ """
    form_class, model = ClientForm, Client
    template_name = 'client/ClientDetailView.html'


class ClientUpdateView(RequireStaffMixin, generic.UpdateView):
    """ """
    form_class, model = ClientForm, Client
    template_name = 'client/ClientUpdateView.html'

    def form_valid(self, form):
        """ """
        old = Client.objects.get(id=self.object.id)
        if not kickstart.client_delete(old):
            return super(ClientUpdateView, self).form_invalid(form)
        if not kickstart.client_create(self, form):
            return super(ClientUpdateView, self).form_invalid(form)
        messages.success(self.request, 'Changes saved!')
        return super(ClientUpdateView, self).form_valid(form)
