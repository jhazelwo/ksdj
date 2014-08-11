from django.db import models
from django.core.validators import RegexValidator

from core.tools import UltraModel

class VLAN(UltraModel):
    """    """
    name = models.CharField(max_length=32)
    network = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15)
    server_ip = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15)
    CIDR_CHOICES = (
        ('28', '255.255.255.240'),
        ('27', '255.255.255.224'),
        ('26', '255.255.255.192'),
        ('25', '255.255.255.128'),
        ('24', '255.255.255.0'),
        ('23', '255.255.254.0'),
        ('22', '255.255.252.0'),
        ('21', '255.255.248.0'),
        ('20', '255.255.240.0'),
        ('19', '255.255.224.0'),
        ('18', '255.255.192.0'),
        ('17', '255.255.128.0'),
    )
    cidr = models.CharField(
        max_length=2,
        choices=CIDR_CHOICES,
        default=None
    )
    # semi-optional, if left blank VLANCreateView will set it to Network.host_first (lowhost)
    gateway = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15, blank=True, null=True)
