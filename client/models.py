# client/models.py

from django.db import models
from django.core.validators import RegexValidator
from django.core.urlresolvers import reverse

from vlan.models import VLAN

from core.tools import UltraModel

foct = '(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[1-9])'
ioct = '(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[1-9]|0)'
reg = '^{foct}\.{ioct}\.{ioct}\.{ioct}$'.format(foct=foct, ioct=ioct)


class Client(UltraModel):
    """
    """
    name = models.CharField(validators=[RegexValidator('^[a-zA-Z][a-zA-Z0-9\.\-\_]+$')],
                            max_length=32,
                            unique=True)  # Hostname
    mac = models.CharField(validators=[RegexValidator('^([a-gA-G0-9]{2}[:-]){5}([a-gA-G0-9]){2}$')],
                           max_length=17,
                           unique=True)  # MAC Address
    ip = models.CharField(validators=[RegexValidator(reg)],
                          max_length=15,
                          blank=True,    # Can be empty in form
                          null=False,    # ...but not in DB
                          unique=True)   # Client IP address
    TYPE_CHOICES = (
        ('01',  'Application'),
        ('02',  'Web'),
        ('03',  'Database'),
        ('04',  'Corp'),
    )
    build_type = models.CharField(
        max_length=2,
        choices=TYPE_CHOICES,
        default=None
    )
    OS_CHOICES = (
        ('el6',  'Ent Linux 6'),
        ('el5',  'Ent Linux 5'),
    )
    os_release = models.CharField(
        max_length=3,
        choices=OS_CHOICES,
        default=None
    )
    #
    # netmask, server_ip and gateway come from vlan
    vlan = models.ForeignKey(VLAN, blank=True, null=True, related_name='client')
    #
    # data for the client's kickstart config file. template in core/skel.py:base_ks
    kickstart_cfg = models.TextField(max_length=16384, default='#')
    
    class Meta:
        ordering = ['-created', ]

    def get_absolute_url(self):
        return reverse('client:detail', kwargs={'pk': self.id})
    
    def save(self, *args, **kwargs):
        """Force hostnames to be lowercase"""
        self.name = self.name.lower()
        self.mac = self.mac.lower()
        super(Client, self).save(*args, **kwargs)
