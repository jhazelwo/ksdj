# human/views.py
from socket import gethostbyname

from django.views import generic
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError

from .mixins import RequireAnonMixin, RequireUserMixin

class Index(RequireUserMixin, generic.ListView):
    """
    User's profile page
    require user is logged in
    If user it not already logged in then do not
        show the friendly error message, just
        direct them to log-in page.
    """
    form_class, model = AuthenticationForm, User
    template_name = 'human/index.html'
    mixin_messages = False


class LoginView(RequireAnonMixin, generic.FormView):
    """ log in page, require no user logged in """
    form_class, model = AuthenticationForm, User
    template_name = 'human/LoginView.html'
    success_url = reverse_lazy('human:index')

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                messages.success(self.request, 'Welcome back!')
                login(self.request, user)
                if self.request.GET.get('next'):
                    self.success_url = self.request.GET['next']
                return super(LoginView, self).form_valid(form)
        return super(LoginView, self).form_invalid(form)


class LogoutView(generic.RedirectView):
    """ Blindly log out any request that hits this url with a GET """
    url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(self.request, 'You have logged out!')
        return super(LogoutView, self).get(request, *args, **kwargs)


class SignupView(RequireAnonMixin, generic.CreateView):
    """ account create, require no logged in user """
    form_class, model = UserCreationForm, User
    template_name = 'human/SignupView.html'
    success_url = reverse_lazy('human:login')

    def form_valid(self, form):
        """
        enforce:
            1. username = valid looking email address
            2. username changed to all lowercase
            3. username is unique as lower
            4. domain part of address resolves in DNS
            5. password size, 8-1024
        
        """
        email = form.cleaned_data['username'].lower()
        passw = form.cleaned_data['password1']
        #
        if User.objects.filter(username=email):
            messages.warning(self.request, 'That email already has an account')
            return super(SignupView, self).form_invalid(form)
        #
        try:
            testing = EmailValidator(whitelist=[])
            user_part, domain_part = email.rsplit('@', 1)
            testing(email)
            gethostbyname(domain_part)
        except Exception as e:
            print(e)
            messages.warning(self.request, 'Please enter a valid email address.')
            return super(SignupView, self).form_invalid(form)
        #
        if len(passw) < 8:
            messages.warning(self.request, 'Password too short! 8 character minimum.')
            return super(SignupView, self).form_invalid(form)
        #
        if len(passw) > 1024:
            messages.warning(self.request, 'Thank you for trying to use a super-long password but unfortunatly it was too long. Please keep it fewer than 1025 characters.')
            return super(SignupView, self).form_invalid(form)
        #
        messages.success(self.request, 'Welcome, {}! Please log in'.format(email))
        form.instance.username = email
        return super(SignupView, self).form_valid(form)
