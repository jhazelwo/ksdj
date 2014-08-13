# vlan/forms.py
from __future__ import absolute_import
from django.forms import ModelForm, RadioSelect
from . import models


class VLANForm(ModelForm):
    class Meta:
        fields = (
            'name',
            'network',
            'cidr',
            'gateway',
            'server_ip',
            'notes',
        )
        model = models.VLAN

    def __init__(self, *args, **kwargs):
        super(VLANForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['size'] = 8
        self.fields['notes'].widget.attrs['rows'] = 2
        self.fields['notes'].widget.attrs['cols'] = 64
