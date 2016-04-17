# vlan/models.py
import os

from django.db import models
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator

from core.tools import UltraModel, ipregex
from fileasobj import FileAsObj

from cfgksdj import KSROOT


class VLAN(UltraModel):
    """
    In the context of this website a VLAN defines a network that the kickstart process serves.
    Clients to be built must be inside a network defined by this model.
    """
    name = models.CharField(validators=[RegexValidator('^[0-9]+$')], max_length=6, unique=True)
    network = models.CharField(validators=[RegexValidator(ipregex)],
                               max_length=15,
                               unique=True)
    server_ip = models.CharField(validators=[RegexValidator(ipregex)],
                                 max_length=15,
                                 blank=True,  # Can be empty in the form,
                                 null=False,  # but must be something in the database.
                                 unique=True)
    gateway = models.CharField(validators=[RegexValidator(ipregex)],
                               max_length=15,
                               blank=True,   # Can be empty in the form,
                               null=False,   # but must be something in the database.
                               unique=True)
    CIDR_CHOICES = (
        ('', ' '),
        ('255.255.255.240', '28'),
        ('255.255.255.224', '27'),
        ('255.255.255.192', '26'),
        ('255.255.255.128', '25'),
        ('255.255.255.0',   '24'),
        ('255.255.254.0',   '23'),
        ('255.255.252.0',   '22'),
        ('255.255.248.0',   '21'),
        ('255.255.240.0',   '20'),
        ('255.255.224.0',   '19'),
        ('255.255.192.0',   '18'),
        ('255.255.128.0',   '17'),
    )
    cidr = models.CharField(
        max_length=15,
        choices=CIDR_CHOICES,
    )
    #
    # Defines if given VLAN is plumbed.
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created', ]

    def get_absolute_url(self):
        return reverse('vlan:detail', kwargs={'pk': self.id})

    def activate(self):
        """
        Update KSROOT/eth1.sh with this VLAN and set self.active to True.
        """
        file = FileAsObj(os.path.join(KSROOT, 'eth1.sh'))
        file.contents = []
        file.add('/sbin/ifconfig eth1 inet {IP} netmask {MASK} up'.format(
            IP=self.server_ip,
            MASK=self.cidr,
        ))
        file.add('/sbin/service dhcpd restart')
        file.write()
        self.active = True
        self.save()
        return
