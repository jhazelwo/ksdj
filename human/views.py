# human/views.py
from socket import gethostbyname

from django.views import generic
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError

from braces.views import AnonymousRequiredMixin

class Index(generic.ListView):
    """ """
    form_class, model = UserCreationForm, User
    template_name = 'human/index.html'


class LoginView(AnonymousRequiredMixin, generic.FormView):
    """ """
    form_class, model = AuthenticationForm, User
    template_name = 'human/LoginView.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)

        if user is not None and user.is_active:
            login(self.request, user)
            return super(LoginView, self).form_valid(form)
        else:
            return self.form_invalid(form)

class LogoutView(generic.RedirectView):
    """ """
    url = reverse_lazy('home')

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(self.request, 'You have logged out!')
        return super(LogoutView, self).get(request, *args, **kwargs)


class UpdateView(generic.FormView):
    """ """
    form_class, model = UserCreationForm, User
    template_name = 'human/UpdateView.html'
    success_url = reverse_lazy('human:index')


class SignupView(AnonymousRequiredMixin, generic.CreateView):
    """ """
    form_class, model = UserCreationForm, User
    template_name = 'human/SignupView.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        """
        enforce:
            1. username = valid looking email address
            2. username changed to all lowercase
            3. username is unique as lower
            4. domain part of address resolves in DNS
            5. password size, 8-64 characters
        
        """
        email = form.cleaned_data['username'].lower()
        if User.objects.filter(username=email):
            messages.warning(self.request, 'That email already has an account')
            return super(SignupView, self).form_invalid(form)
        try:
            testing = EmailValidator(whitelist=[])
            testing.whitelist = []
            user_part, domain_part = email.rsplit('@', 1)
            testing(email)
            gethostbyname(domain_part)
        except Exception as e:
            print(e)
            messages.warning(self.request, 'Please enter a valid email address.')
            return super(SignupView, self).form_invalid(form)
        messages.success(self.request, 'Welcome!')
        form.instance.username = email
        return super(SignupView, self).form_invalid(form)
