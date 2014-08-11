# vlan/forms.py
from __future__ import absolute_import
from django.forms import ModelForm, RadioSelect
from . import models


class VLANForm(ModelForm):
    class Meta:
        fields = (
            'name',
            'network',
            'gateway',
            'cidr',
            'server_ip',
        )
        model = models.VLAN
        widgets = {
            'cidr' : RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super(VLANForm, self).__init__(*args, **kwargs)
        self.fields['cidr'].empty_label = None
