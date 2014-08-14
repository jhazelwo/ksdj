from django.db import models
from django.core.validators import RegexValidator
from django.core.urlresolvers import reverse

from vlan.models import VLAN

from core.tools import UltraModel

class Client(UltraModel):
    """
    """
    name = models.CharField(validators=[RegexValidator('^[a-zA-Z0-9\.\-\_]+$')], max_length=32, unique=True) # Hostname
    mac = models.CharField(validators=[RegexValidator('^([a-gA-G0-9]{2}[:-]){5}([a-gA-G0-9]){2}$')], max_length=17, unique=True) # MAC Address
    ip = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15, blank=True, null=False, unique=True)
    TYPE_CHOICES = (
        ('01',  'Application'),
        ('02',  'Web'),
        ('03',  'Database'),
        ('04',  'Corp'),
    )
    build_type = models.CharField(
        max_length=2,
        choices=TYPE_CHOICES,
        #default=TYPE_CHOICES[0][0]
        default=None
    )
    OS_CHOICES = (
        ('el6',  'Ent Linux 6'),
        ('el5',  'Ent Linux 5'),
    )
    os_release = models.CharField(
        max_length=3,
        choices=OS_CHOICES,
        #default=OS_CHOICES[0][0]
        default=None
    )
    #
    # netmask, server_ip and gateway come from vlan
    vlan = models.ForeignKey(VLAN, blank=True, null=True, related_name='client')

    def get_absolute_url(self):
        return reverse('client:detail', kwargs={'pk': self.id})

    def save(self, *args, **kwargs):
        """Force hostnames to be lowercase"""
        self.name = self.name.lower()
        self.mac = self.mac.lower()
        super(Client, self).save(*args, **kwargs)

