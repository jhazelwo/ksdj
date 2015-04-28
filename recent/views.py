# recent/views.py

from django.views import generic

from human.mixins import RequireStaffMixin

from . import models


class Index(RequireStaffMixin, generic.ListView):
    model = models.Log
    template_name = 'recent/index.html'


class RecentDetailView(RequireStaffMixin, generic.DetailView):
    model = models.Log
    template_name = 'recent/LogDetail.html'
