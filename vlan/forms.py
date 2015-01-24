# vlan/forms.py
from django.forms import ModelForm
from . import models


class Update(ModelForm):
    class Meta:
        fields = (
            'name',
            'network',
            'cidr',
            'gateway',
            'server_ip',
            'notes',
            'active',
        )
        model = models.VLAN

    def __init__(self, *args, **kwargs):
        super(Update, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['size'] = 8
        self.fields['notes'].widget.attrs['rows'] = 2
        self.fields['notes'].widget.attrs['cols'] = 64


class LockedUpdate(ModelForm):
    class Meta:
        fields = (
            'notes',
            'active',
        )
        model = models.VLAN
    
    def __init__(self, *args, **kwargs):
        super(LockedUpdate, self).__init__(*args, **kwargs)
        self.fields['notes'].widget.attrs['rows'] = 2
        self.fields['notes'].widget.attrs['cols'] = 64


class Create(ModelForm):
    class Meta:
        fields = (
            'name',
            'network',
            'cidr',
            'notes',
            'active',
        )
        model = models.VLAN

    def __init__(self, *args, **kwargs):
        super(Create, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['size'] = 8
        self.fields['notes'].widget.attrs['rows'] = 2
        self.fields['notes'].widget.attrs['cols'] = 64
