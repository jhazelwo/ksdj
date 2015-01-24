# vlan/views.py

from django.views import generic
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy

from core import kickstart, ipcalc
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
    template_name = 'vlan/VLANCreateView.html'

    def form_invalid(self, form):
        messages.warning(self.request, 'Error! Please check your input.')
        return super(VLANCreateView, self).form_invalid(form)
    
    def form_valid(self, form):
        """
        This is ugly, fo reals, like so ugly.
        """
        self.object = form.save(commit=False)
        if form.cleaned_data['active']:
            VLAN.objects.all().update(active=False)
            self.object.activate(self.request)
        try:
            netinfo = ipcalc.Network('%s/%s' % (form.cleaned_data['network'], form.cleaned_data['cidr']))
        except Exception as e:
            messages.error(s.request, 'Failed to determine network information from data provided. - %s' % e, extra_tags='danger')
            return False
        form.cleaned_data['network'] = self.object.network = netinfo.network()
        form.cleaned_data['gateway'] = self.object.gateway = netinfo.host_first()
        form.cleaned_data['server_ip'] = self.object.server_ip = ipcalc.IP(int(netinfo.host_last()) - 2, version=4)
        if not kickstart.vlan_create(self, form):
            return super(VLANCreateView, self).form_invalid(form)
        messages.success(self.request, 'VLAN {0} added to Kickstart!'.format(self.object))
        log_form_valid(self, form)
        return super(VLANCreateView, self).form_valid(form)


class VLANDetailView(generic.DetailView):
    """ View a VLAN's details """
    model = VLAN
    template_name = 'vlan/VLANDetailView.html'
    
    def get_context_data(self, **kwargs):
        context = super(VLANDetailView, self).get_context_data(**kwargs)
        context['related'] = Client.objects.filter(vlan=self.object.id)
        return context


class VLANUpdateView(RequireStaffMixin, generic.UpdateView):
    """
    Edit a Kickstart VLAN
    If there are clients using this vlan, give warning and do not allow IP changes, only notes.
    """
    form_class, model = forms.Update, VLAN
    template_name = 'vlan/VLANUpdateView.html'
    
    def get_form_class(self):
        """
        If there are any clients using this vlan
        then render most of the fields as disabled
        Additional enforcement exists in form_valid()
        """
        # if Client.objects.filter(vlan=self.object.id).count():
        if self.object.client.count() is not 0:
            return forms.LockedUpdate
        else:
            return forms.Update

    def form_invalid(self, form):
        """
        I know these look redundant but I have run into very weird
        failure states in the past where having this pretty error
        would have saved me a lot of time.
        """
        messages.warning(self.request, 'Error! Please check your input.')
        return super(VLANUpdateView, self).form_invalid(form)
    
    def form_valid(self, form):
        """
        DJ will take care of updating the database all we have to do is delete the vlan conf update the dhcpd config
        then create them again with the form data
        
        The kickstart.vlan_ functions will generate error messages as needed.
        """
        #
        if self.object.client.count() is 0:
            self.old = VLAN.objects.get(id=self.object.id)
            if not kickstart.vlan_delete(self):
                return super(VLANUpdateView, self).form_invalid(form)
            if not kickstart.vlan_create(self, form):
                return super(VLANUpdateView, self).form_invalid(form)
        #
        if form.cleaned_data['active']:
            VLAN.objects.all().update(active=False)
            self.object.activate(self.request)
        #
        messages.success(self.request, 'Changes saved!')
        log_form_valid(self, form)
        return super(VLANUpdateView, self).form_valid(form)


class VLANDeleteView(generic.DeleteView):
    """ Delete a VLAN """
    model = VLAN
    template_name = 'vlan/VLANDeleteView.html'
    success_url = reverse_lazy('vlan:index')

    def delete(self, request, *args, **kwargs):
        self.old = self.get_object()
        if self.old.client.count() is not 0:
            messages.error(self.request, 'Unable to comply, there are clients in this vlan!', extra_tags='danger')
            return super(VLANDeleteView, self).get(request, *args, **kwargs)
        if not kickstart.vlan_delete(self):
            return super(VLANDeleteView, self).get(request, *args, **kwargs)
        messages.success(self.request, 'VLAN {0} removed!'.format(self.old))
        return super(VLANDeleteView, self).delete(request, *args, **kwargs)
