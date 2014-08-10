# client/forms.py
from __future__ import absolute_import
from django.forms import ModelForm, RadioSelect
from . import models


class ClientForm(ModelForm):
    class Meta:
        fields = (
            'name',
            'mac',
            'ip',
            'build_type',
            'os_release',
            'vlan',
            )
        model = models.Client
        widgets = {
            'vlan' : RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        self.fields['vlan'].empty_label = None
