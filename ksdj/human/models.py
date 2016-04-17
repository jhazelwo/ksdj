# human/models.py

from django.db import models
from django.core.validators import RegexValidator
from django.core.urlresolvers import reverse

from core.tools import UltraModel


class Event(UltraModel):
    """ """
    name = models.CharField(max_length=256)
    ip = models.CharField(max_length=256)
    user = models.CharField(max_length=256)
    
    def get_absolute_url(self):
        return reverse('recent:detail', kwargs={'pk': self.id})
