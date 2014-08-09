from django.db import models
from django.core.validators import RegexValidator

from core.tools import UltraModel

class VLAN(UltraModel):
    """
    """
    name = models.CharField(max_length=32)
    network = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15)
    quadmask = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15)
    cidr = models.CharField(max_length=2)
    server_ip = models.CharField(validators=[RegexValidator('^((\d){1,3}.){3}(\d){1,3}$')], max_length=15)
