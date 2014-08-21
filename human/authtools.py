# human/authtools.py

from django.contrib import messages

"""

I want to `fail` at the last possible step, usually right before
a database or real file is updated.



"""

def user_and_staff(s):
    """
    Require:
        User logged in
        User is_staff 
    """
    if not s.request.user.is_authenticated():
        messages.error(s.request, 'Unable to comply, please log in.', extra_tags='danger')
        return False
    if s.request.user.is_authenticated():
        if not s.request.user.is_staff:
            messages.error(s.request, 'Unable to comply, your account it now allowed to use this tool.', extra_tags='danger')
            return False
    return True
