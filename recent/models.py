# recent/models.py

from django.db import models
from django.core.validators import RegexValidator
from django.core.urlresolvers import reverse

from core.tools import UltraModel


class Log(models.Model):
    """ """
    user_name = models.CharField(max_length=1024, blank=True, null=True)
    model_name = models.CharField(max_length=1024, blank=True, null=True)
    view_name = models.CharField(max_length=1024, blank=True, null=True)
    object_name = models.CharField(max_length=1024, blank=True, null=True)
    when = models.DateTimeField(auto_now_add=True) # now()
    verbose = models.CharField(max_length=1024, blank=True, null=True)    # request.POST
    
    def __str__(self):
        return '{} {} {}'.format(self.user_name,self.view_name,self.object_name)
