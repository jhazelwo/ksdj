# vlan/models.py
import os

from django.db import models
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.core.validators import RegexValidator

from core.tools import UltraModel
from core.fileasobj import FileAsObj

from cfgksdj import KSROOT


class VLAN(UltraModel):
    """    """
    name = models.CharField(validators=[RegexValidator('^[0-9]+$')], max_length=6, unique=True)
    network = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15, unique=True)
    server_ip = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15, unique=True)
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
    # semi-optional, if left blank VLANCreateView will set it to Network.host_first (low host)
    gateway = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')],
                               max_length=15,
                               blank=True,
                               null=False,
                               unique=True)
    #
    # Defines if given VLAN is plumbed.
    active = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('vlan:detail', kwargs={'pk': self.id})

    def activate(self, request):
        """
        Update KSROOT/eth1.sh with this VLAN and set self.active to True.
        """
        this_file = FileAsObj(os.path.join(KSROOT, 'eth1.sh'))
        this_file.contents = []
        this_file.add('/sbin/ifconfig eth1 inet {IP} netmask {MASK} up'.format(
            IP=self.server_ip,
            MASK=self.cidr,
        ))
        this_file.add('/sbin/service dhcpd restart')
        this_file.write()

        if this_file.Errors:
            messages.error(request, this_file.Trace, extra_tags='danger')
            return False
        self.active = True
        self.save()
        return True
