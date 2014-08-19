# vlan/views.py

from django.views import generic
from django.contrib import messages

from braces.views import LoginRequiredMixin, StaffuserRequiredMixin


from core import kickstart

from client.models import Client

from vlan.models import VLAN

from .forms import VLANForm, VLANLockedForm
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


class VLANUpdateView(LoginRequiredMixin,
                    StaffuserRequiredMixin,
                    generic.UpdateView):
    """ Edit a Kickstart VLAN
    
    If there are clients using this vlan, give warning
    and do not allow IP changes, only notes.
    
    """
    form_class, model = VLANForm, VLAN
    template_name = 'vlan/VLANUpdateView.html'
    raise_exception = True   
    
    def get_form_class(self):
        """
        If there are any clients using this vlan
        then render most of the fields as disabled
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
        """ """
        messages.warning(self.request, 'Error! Please check your input.')
        return super(VLANUpdateView, self).form_invalid(form)
    
    def form_valid(self, form):
        """ """
        count = Client.objects.filter(vlan=self.object.id).count()
        if count > 0:
            for this in ['name','network','cidr','gateway','server_ip']:
                if this in form.cleaned_data:
                    messages.error(self.request, 'VLAN is being used by one or more clients, unable to change.', extra_tags='danger')
                    return super(VLANUpdateView, self).form_invalid(form)
        if 'name' in form.cleaned_data and count < 1:
            self.old = VLAN.objects.get(id=self.object.id)
            if not kickstart.vlan_update(self, form):
                return super(VLANUpdateView, self).form_invalid(form)
        messages.success(self.request, 'Changes saved!')
        return super(VLANUpdateView, self).form_valid(form)
