# core/views.py

from django.shortcuts import render
from django.views import generic
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages

from .forms import LoginForm

class Index(generic.TemplateView):
    """  """
    template_name = 'core/index.html'


class LoginFormView(generic.FormView):
    """ """
    form_class = LoginForm
    template_name = 'core/login.html'
    
    def form_valid(self, form):
        """ __love__ """
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            login(self.request, user)
            return super(LoginFormView, self).form_valid(form)
        else:
            messages.error(self.request, 'Authentication failed!')
            return self.form_invalid(form)


class LogoutFormView(generic.FormView):
    """ """
    def get(self, request, *args, **kwargs):
        logout(request)
        return super(LogoutFormView, self).get(request, *args, **kwargs)

