# vlan/views.py

from django.views import generic
from django.contrib import messages

from core import kickstart

from vlan.models import VLAN

from .forms import VLANForm
from .models import VLAN


class Index(generic.ListView):
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
        """ """
        if not kickstart.vlan_create(self, form):
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

    def form_invalid(self,form):
        messages.warning(self.request, 'Error! Please check your input.')
        return super(VLANUpdateView, self).form_invalid(form)
    
    def form_valid(self, form):
        """ """
        if not kickstart.vlan_update(self, form):
            return super(VLANUpdateView, self).form_invalid(form)
        messages.success(self.request, 'Changes saved!')
        return super(VLANUpdateView, self).form_valid(form)
