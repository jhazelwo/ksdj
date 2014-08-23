# human/authtools.py

from django.contrib import messages

def user_and_staff(s):
    """
    Require:
        User logged in
        User is_staff
        
    s = `self` of object that called this function
    """
    if not s.request.user.is_authenticated():
        messages.warning(s.request, 'Unable to comply, please log in.')
        return False
    if s.request.user.is_authenticated():
        if not s.request.user.is_staff:
            messages.warning(s.request, 'Unable to comply, your account is not allowed to use this tool.')
            return False
    return True

def no_user(s):
    """
    Require:
        no user logged in
        
    s = `self` of object that called this function
    """
    if s.request.user.is_authenticated():
        return False
    return True
