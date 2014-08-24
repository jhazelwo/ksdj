# vlan/views.py

from django.views import generic
from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from core import kickstart
from human import authtools
from human.mixins import RequireStaffMixin

from client.models import Client
from vlan.models import VLAN

from .forms import VLANForm, VLANLockedForm
from .models import VLAN


class Index(generic.ListView):
    """ A list of existing VLANs """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/index.html'


class VLANCreateView(RequireStaffMixin, generic.CreateView):
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


class VLANUpdateView(RequireStaffMixin, generic.UpdateView):
    """ Edit a Kickstart VLAN
    
    If there are clients using this vlan, give warning
    and do not allow IP changes, only notes.
    
    """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/VLANUpdateView.html'
    
    def get_form_class(self):
        """
        If there are any clients using this vlan
        then render most of the fields as disabled
        Additional enforcement exists in form_valid()
        """
        if Client.objects.filter(vlan=self.object.id).count():
            return VLANLockedForm
        else:
            return VLANForm
    
    def get_context_data(self, **kwargs):
        """  """
        context = super(VLANUpdateView, self).get_context_data(**kwargs)
        count = Client.objects.filter(vlan=self.object.id).count()
        context['related'] = count
        return context

    def form_invalid(self,form):
        """
        I know these look redundant but I have run into very weird
        failure states in the past where having this pretty error
        would have saved me a lot of time.
        """
        messages.warning(self.request, 'Error! Please check your input.')
        return super(VLANUpdateView, self).form_invalid(form)
    
    def form_valid(self, form):
        """
        DJ will take care of updating the database
        all we have to do is delete the vlan conf
        update the dhcpd config then create them
        again with the form data
        
        The kickstart.vlan_ functions will generate
        error messages as needed. 
        """
        count = Client.objects.filter(vlan=self.object.id).count()
        if count > 0:
            for this in ['name','network','cidr','gateway','server_ip']:
                if this in form.cleaned_data:
                    messages.error(self.request, 'VLAN is being used by one or more clients, unable to change.', extra_tags='danger')
                    return super(VLANUpdateView, self).form_invalid(form)
        #
        if 'name' in form.cleaned_data and count < 1:
            old = VLAN.objects.get(id=self.object.id)
            if not kickstart.vlan_delete(old):
                return super(VLANUpdateView, self).form_invalid(form)
            if not kickstart.vlan_create(self, form):
                return super(VLANUpdateView, self).form_invalid(form)
        messages.success(self.request, 'Changes saved!')
        return super(VLANUpdateView, self).form_valid(form)
