# core/tools.py

import logging

from django.db import models
from django.contrib import messages


class UltraModel(models.Model):
    """
    A wrapper model. All models should inherit this. 
    """
    created = models.DateTimeField(auto_now_add=True) # Born
    modified = models.DateTimeField(auto_now=True)     # last changed
    #
    # These are optional fields, but should be valid for
    # nearly everything.
    doc_url = models.URLField(blank=True, null=True)   # A URL to external/wiki documentatoin about the object.
    notes = models.TextField(blank=True, null=True)  # Comments/notes about the object

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.name)


def featherfail(view=False, msg=False):
    """
    Feather Fail. Show pretty error message a log it.

    view is a view object that must have valid user.
    msg is just a string
    """
    try:
        messages.error(view.request, msg, extra_tags='danger')
        logging.error('[{0}@{1}] {2}'.format(view.request.user, view.__class__.__name__, msg))
    except:
        print(msg)
    return
