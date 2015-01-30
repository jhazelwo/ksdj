# vlan/views.py

from django.views import generic
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy

from core import kickstart, ipcalc
from core.tools import featherfail
from human.mixins import RequireStaffMixin
from recent.functions import log_form_valid

from client.models import Client

from . import forms
from .models import VLAN


class Index(generic.ListView):
    """ A list of existing VLANs """
    model = VLAN
    template_name = 'vlan/index.html'


class VLANCreateView(RequireStaffMixin, generic.CreateView):
    """ Add a VLAN to Kickstart """
    form_class, model = forms.Create, VLAN
    template_name = 'vlan/create.html'

    def form_valid(self, form):
        """
        """
        self.object = form.save(commit=False)
        try:
            form = kickstart.vlan_create(form)
            if form.cleaned_data['active']:
                VLAN.objects.all().update(active=False)
                self.object.activate()
            messages.success(self.request, 'VLAN {0} added to Kickstart!'.format(self.object))
            log_form_valid(self, form)
            return super(VLANCreateView, self).form_valid(form)
        except Exception as msg:
            featherfail(self, msg)
        return super(VLANCreateView, self).form_invalid(form)


class VLANDetailView(generic.DetailView):
    """ View a VLAN's details """
    model = VLAN
    template_name = 'vlan/detail.html'
    
    def get_context_data(self, **kwargs):
        context = super(VLANDetailView, self).get_context_data(**kwargs)
        context['related'] = Client.objects.filter(vlan=self.object.id)
        return context


class VLANUpdateView(RequireStaffMixin, generic.UpdateView):
    """
    Edit a Kickstart VLAN
    """
    form_class, model = forms.Update, VLAN
    template_name = 'vlan/update.html'
    
    def get_form_class(self):
        """
        If there are any clients using this vlan then render most of the fields as disabled
        """
        if self.object.client.count() is not 0:
            return forms.LockedUpdate
        else:
            return forms.Update

    def form_valid(self, form):
        """
        Dj says the data is OK, so ask kickstart.py to update the files.
        """
        try:
            if self.object.client.count() is 0:
                kickstart.vlan_delete(self.object)
                form = kickstart.vlan_create(form)
            if form.cleaned_data['active']:
                VLAN.objects.all().update(active=False)
                self.object.activate()
            messages.success(self.request, 'Changes saved!')
            log_form_valid(self, form)
            return super(VLANUpdateView, self).form_valid(form)
        except Exception as msg:
            featherfail(self, msg)
        return super(VLANUpdateView, self).form_invalid(form)


class VLANDeleteView(generic.DeleteView):
    """ Delete a VLAN """
    model = VLAN
    template_name = 'vlan/delete.html'
    success_url = reverse_lazy('vlan:index')

    def delete(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
            kickstart.vlan_delete(obj)
            messages.success(self.request, 'VLAN {0} removed!'.format(obj))
            return super(VLANDeleteView, self).delete(request, *args, **kwargs)
        except Exception as msg:
            featherfail(self, msg)
        return super(VLANDeleteView, self).get(request, *args, **kwargs)
