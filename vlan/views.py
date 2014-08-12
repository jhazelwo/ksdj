# vlan/views.py
from __future__ import absolute_import

from django.views import generic
from django.contrib import messages

# https://github.com/tehmaze/ipcalc (ported to py3)
from core import ipcalc
from core.functions import vlancreate

from vlan.models import VLAN

from .forms import VLANForm
from .models import VLAN


class Index(generic.TemplateView):
    """ default /vlan/ view """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/index.html'


class VLANCreateView(generic.CreateView):
    """ """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/VLANCreateView.html'

    def form_invalid(self,form):
        messages.warning(self.request, 'Error! Please check your input.')
        return super(VLANCreateView, self).form_invalid(form)
    
    def form_valid(self, form):
        """
        Finish up data validation then hand the
        form/object data to 'core' to create/update
        the actual kickstart files.
        """
        n = form.cleaned_data['network']
        c = form.cleaned_data['cidr']
        i = form.cleaned_data['server_ip']
        netinfo = ipcalc.Network('%s/%s' % (n,c))
        if i not in netinfo:
            messages.errowarningr(self.request, 'IP address %s is not inside network %s/%s!' % (i,n,c))
            return super(VLANCreateView, self).form_invalid(form)
        if not form.cleaned_data['gateway']:
            form.instance.gateway = netinfo.host_first()
        result = vlancreate(form)
        if not result:
            messages.error(self.request, 'Failed to complete file updates. VLAN not added. Have the Kickstart admin check logs.', extra_tags='danger' )
            return super(VLANCreateView, self).form_invalid(form)
        messages.success(self.request, 'VLAN %s added to Kickstart!' % form.cleaned_data['name'])
        return super(VLANCreateView, self).form_valid(form)


class VLANDetailView(generic.DetailView):
    """ """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/VLANDetailView.html'


class VLANUpdateView(generic.UpdateView):
    """ """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/VLANUpdateView.html'
