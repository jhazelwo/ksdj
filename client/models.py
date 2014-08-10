from django.db import models
from django.core.validators import RegexValidator

from vlan.models import VLAN

from core.tools import UltraModel

class Client(UltraModel):
    """
    """
    name = models.CharField(validators=[RegexValidator('^[a-zA-Z0-9\.\-\_]+$')], max_length=32, unique=True) # Hostname
    mac = models.CharField(validators=[RegexValidator('^([a-gA-G0-9]{2}[:-]){5}([a-gA-G0-9]){2}$')], max_length=17, unique=True) # MAC Address
    ip = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15, unique=True)
    TYPE_CHOICES = (
        ('01',  'Application'),
        ('02',  'Web'),
        ('03',  'Database'),
        ('04',  'Corp'),
    )
    build_type = models.CharField(
        max_length=2,
        choices=TYPE_CHOICES,
        default=TYPE_CHOICES[0][0]
    )
    OS_CHOICES = (
        ('01',  'el6'),
        ('02',  'el5'),
    )
    os_release = models.CharField(
        max_length=2,
        choices=OS_CHOICES,
        default=OS_CHOICES[0][0]
    )
    #
    # netmask, server_ip and gateway come from vlan
    vlan = models.ForeignKey(VLAN, related_name='client')

    def get_absolute_url(self):
        return reverse('client:detail', kwargs={'pk': self.id})

    def save(self, *args, **kwargs):
        """Force hostnames to be lowercase"""
        self.name = self.name.lower()
        super(Client, self).save(*args, **kwargs)

