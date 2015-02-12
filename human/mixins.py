# human/mixins.py

from django.shortcuts import redirect
from django.contrib import messages
from django.core.urlresolvers import reverse


class RequireAnonMixin(object):
    """
    Require user NOT logged in
    I will redirect to success_url if it is set, otherwise the human.url('home')
    """
    # mixin_messages = True ## in prod this does not generate messages

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            if self.success_url:
                messages.info(self.request, 'redirected success_url {0}'.format(self.success_url))
                return redirect(self.success_url)
            messages.info(self.request, 'redirected to home')
            return redirect(reverse('home'))
        return super(RequireAnonMixin, self).dispatch(request, *args, **kwargs)


class RequireStaffMixin(object):
    """ Require user logged in AND is_staff """
    mixin_messages = True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            if self.mixin_messages:
                messages.warning(request, 'Unable to comply, please log in.')
            return redirect('{0}?next={1}'.format(reverse('human:login'), request.path))
        if request.user.is_authenticated():
            if not request.user.is_staff:
                if self.mixin_messages:
                    messages.warning(request, 'Unable to comply, your account is not allowed to use this tool.')
                return redirect('{0}?next={1}'.format(reverse('human:index'), request.path))
        return super(RequireStaffMixin, self).dispatch(request, *args, **kwargs)


class RequireUserMixin(object):
    """ Require user logged in """
    mixin_messages = True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            if self.mixin_messages:
                messages.warning(request, 'Unable to comply, please log in.')
            return redirect('{0}?next={1}'.format(reverse('human:login'), request.path))
        return super(RequireUserMixin, self).dispatch(request, *args, **kwargs)
