# client/views.py

from django.views import generic
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy

from core import kickstart
from core.tools import featherfail
from human.mixins import RequireStaffMixin
from recent.functions import log_form_valid

from vlan.models import VLAN

from .forms import ClientForm, CustomForm
from .models import Client


class Index(generic.ListView):
    """ List of existing kickstart clients """
    form_class, model = ClientForm, Client
    template_name = 'client/index.html'


class Detail(generic.DetailView):
    """ View details of a client """
    form_class, model = ClientForm, Client
    template_name = 'client/detail.html'


class Custom(RequireStaffMixin, generic.UpdateView):
    """ Edit the kickstart config file for a client """
    form_class, model = CustomForm, Client
    template_name = 'client/custom.html'

    def form_valid(self, form):
        try:
            form = kickstart.update_kickstart_file(form)
            log_form_valid(self)
            messages.success(self.request, 'Changes saved!')
            return super(Custom, self).form_valid(form)
        except Exception as msg:
            featherfail(self, msg)
        return super(Custom, self).form_invalid(form)


class Create(RequireStaffMixin, generic.CreateView):
    """ Add a client to kickstart """
    form_class, model = ClientForm, Client
    template_name = 'client/create.html'

    def get_context_data(self, **kwargs):
        context = super(Create, self).get_context_data(**kwargs)
        context['vlans'] = VLAN.objects.all()
        return context

    def form_valid(self, form):
        try:
            form = kickstart.client_create(form)
            log_form_valid(self)
            messages.success(self.request, 'Client added to kickstart!')
            return super(Create, self).form_valid(form)
        except Exception as msg:
            featherfail(self, msg)
        return super(Create, self).form_invalid(form)


class Update(RequireStaffMixin, generic.UpdateView):
    """ Edit a kickstart client """
    form_class, model = ClientForm, Client
    template_name = 'client/update.html'

    def get_context_data(self, **kwargs):
        context = super(Update, self).get_context_data(**kwargs)
        context['vlans'] = VLAN.objects.all()
        return context

    def form_valid(self, form):
        try:
            old = Client.objects.get(id=self.object.id)
            kickstart.client_delete(old)
            form = kickstart.client_create(form, old)
            log_form_valid(self)
            messages.success(self.request, 'Changes saved!')
            return super(Update, self).form_valid(form)
        except Exception as msg:
            featherfail(self, msg)
        return super(Update, self).form_invalid(form)


class Delete(generic.DeleteView):
    """ Delete a client """
    form_class, model = ClientForm, Client
    template_name = 'client/delete.html'
    success_url = reverse_lazy('client:index')

    def delete(self, request, *args, **kwargs):
        self.old = self.get_object()
        try:
            kickstart.client_delete(self.old)
            log_form_valid(self)
            messages.success(self.request, 'Client {0} removed!'.format(self.old.name))
            return super(Delete, self).delete(request, *args, **kwargs)
        except Exception as msg:
            featherfail(self, msg)
        return super(Delete, self).get(request, *args, **kwargs)
