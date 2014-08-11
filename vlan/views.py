# vlan/views.py
from __future__ import absolute_import

from django.views import generic
from django.contrib import messages

# https://github.com/tehmaze/ipcalc (ported to py3)
from core import ipcalc

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

    def form_valid(self, form):
        """
        Here be dragons!
        """
        n = form.cleaned_data['network']
        c = form.cleaned_data['cidr']
        i = form.cleaned_data['server_ip']
        netinfo = ipcalc.Network('%s/%s' % (n,c))
        if i not in netinfo:
            messages.warning(self.request, 'IP address %s is not inside network %s/%s!' % (i,n,c) )
            print('IP address %s is not inside network %s/%s!' % (i,n,c) )
        if not form.cleaned_data['gateway']:
            print(dir(form))
            form.instance.gateway = netinfo.host_first()
        #messages.success(self.request, 'VLAN added to kickstart!')
        return super(VLANCreateView, self).form_valid(form)


class VLANDetailView(generic.DetailView):
    """ """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/VLANDetailView.html'


class VLANUpdateView(generic.UpdateView):
    """ """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/VLANUpdateView.html'
