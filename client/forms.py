# client/forms.py
from __future__ import absolute_import

import os

from django.forms import Form, ModelForm, RadioSelect, Textarea, CharField
from django.contrib import messages
from . import models

from core.settings import KS_CONF_DIR
from core.fileasobj import FileAsObj


class ClientForm(ModelForm):
    class Meta:
        fields = (
            'name',
            'mac',
            'ip',
            'build_type',
            'os_release',
            'vlan',
            'notes',
            )
        model = models.Client
        widgets = {
            'build_type' : RadioSelect(),
            'os_release' : RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super(ClientForm, self).__init__(*args, **kwargs)
        self.fields['vlan'].empty_label = '<auto-detect>'
        self.fields['notes'].widget.attrs['rows'] = 2
        self.fields['notes'].widget.attrs['cols'] = 64

class CustomForm(ModelForm):
    kickstart_file = CharField(widget=Textarea)
    class Meta:
        fields = (
            'kickstart_file',
        )
        model = models.Client

    def __init__(self, *args, **kwargs):
        super(CustomForm, self).__init__(*args, **kwargs)
        fname = os.path.join(KS_CONF_DIR,'%s.ks' % self.instance.name)
        this_file = FileAsObj(fname, verbose=True)
        if this_file.Errors:
            self.fields['kickstart_file'].initial = this_file.Trace
        else:
            self.fields['kickstart_file'].initial = this_file
        self.fields['kickstart_file'].widget.attrs['rows'] = 32
        self.fields['kickstart_file'].widget.attrs['style'] = 'width: 100%; background-color: #FFB8B8'        
        self.fields['kickstart_file'].widget.attrs['wrap'] = 'off'
