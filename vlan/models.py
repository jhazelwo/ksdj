from django.db import models
from django.core.validators import RegexValidator
from django.core.urlresolvers import reverse

from core.tools import UltraModel

class VLAN(UltraModel):
    """    """
    name = models.CharField(validators=[RegexValidator('^[0-9]+$')], max_length=6, unique=True)
    network = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15, unique=True)
    server_ip = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15, unique=True)
    CIDR_CHOICES = (
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
    # semi-optional, if left blank VLANCreateView will set it to Network.host_first (lowhost)
    gateway = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15, blank=True, null=True, unique=True)

    def get_absolute_url(self):
        return reverse('vlan:detail', kwargs={'pk' : self.id})
    