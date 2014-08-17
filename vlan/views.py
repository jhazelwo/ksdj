# vlan/views.py

from django.views import generic
from django.contrib import messages

from core import kickstart

from client.models import Client

from vlan.models import VLAN

from .forms import VLANForm
from .models import VLAN


class Index(generic.ListView):
    """ A list of existing VLANs """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/index.html'


class VLANCreateView(generic.CreateView):
    """ Add a VLAN to Kickstart """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/VLANCreateView.html'

    def form_invalid(self,form):
        """ """
        messages.warning(self.request, 'Error! Please check your input.')
        return super(VLANCreateView, self).form_invalid(form)
    
    def form_valid(self, form):
        """ """
        if not kickstart.vlan_create(self, form):
            return super(VLANCreateView, self).form_invalid(form)
        messages.success(self.request, 'VLAN %s added to Kickstart!' % form.cleaned_data['name'])
        return super(VLANCreateView, self).form_valid(form)


class VLANDetailView(generic.DetailView):
    """ View a VLAN's details """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/VLANDetailView.html'
    
    def get_context_data(self, **kwargs):
        context = super(VLANDetailView, self).get_context_data(**kwargs)
        context['related'] = Client.objects.filter(vlan=self.object.id)
        return context


class VLANUpdateView(generic.UpdateView):
    """ Edit a Kickstart VLAN
    
    If there are clients using this vlan, give warning
    and do not allow IP changes, only notes.
    
    """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/VLANUpdateView.html'

    def form_invalid(self,form):
        """ """
        messages.warning(self.request, 'Error! Please check your input.')
        return super(VLANUpdateView, self).form_invalid(form)
    
    def form_valid(self, form):
        """ """
        if not kickstart.vlan_update(self, form):
            return super(VLANUpdateView, self).form_invalid(form)
        messages.success(self.request, 'Changes saved!')
        return super(VLANUpdateView, self).form_valid(form)
