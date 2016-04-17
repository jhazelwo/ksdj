# human/authtools.py
from socket import gethostbyname

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.validators import EmailValidator

# Once again, we should NOT be storing user passwords but since I have to, I guess this is the next phase
# This is the top 100 most common passwords from the recent Adobe breach.
common_passwords = ['000000',
                    '102030',
                    '111111',
                    '11111111',
                    '112233',
                    '121212',
                    '123123',
                    '123123123',
                    '123321',
                    '1234',
                    '12345',
                    '123456',
                    '1234567',
                    '12345678',
                    '123456789',
                    '1234567890',
                    '123654',
                    '123qwe',
                    '1q2w3e',
                    '1q2w3e4r',
                    '1qaz2wsx',
                    '222222',
                    '555555',
                    '654321',
                    '666666',
                    '753951',
                    '7777777',
                    '987654321',
                    'aaaaaa',
                    'abc',
                    'abc123',
                    'abcd1234',
                    'abcdef',
                    'adobe1',
                    'adobe123',
                    'adobeadobe',
                    'alexander',
                    'andrea',
                    'andrew',
                    'asdasd',
                    'asdfasdf',
                    'asdfgh',
                    'asdfghj',
                    'asdfghjkl',
                    'azerty',
                    'baseball',
                    'buster',
                    'charlie',
                    'chocolate',
                    'computer',
                    'daniel',
                    'dragon',
                    'dreamweaver',
                    'fdsa',
                    'football',
                    'freedom',
                    'fuckyou',
                    'ginger',
                    'hannah',
                    'iloveyou',
                    'internet',
                    'jennifer',
                    'jessica',
                    'jordan',
                    'joshua',
                    'killer',
                    'letmein',
                    'liverpool',
                    'macromedia',
                    'maggie',
                    'master',
                    'matrix',
                    'michael',
                    'michelle',
                    'monkey',
                    'nicole',
                    'password',
                    'password1',
                    'pepper',
                    'photoshop',
                    'princess',
                    'purple',
                    'qazwsx',
                    'qwerty',
                    'qwertyuiop',
                    'samsung',
                    'secret',
                    'shadow',
                    'snoopy1',
                    'soccer',
                    'summer',
                    'sunshine',
                    'superman',
                    'test',
                    'thomas',
                    'tigger',
                    'trustno1',
                    'welcome',
                    'whatever',
                    'zxcvbnm']


def user_and_staff(view):
    """
    Require:
        User logged in
        User is_staff
        
    view = `self` of view object that called this function
    """
    if not view.request.user.is_authenticated():
        messages.warning(s.request, 'Unable to comply, please log in.')
        return False
    if view.request.user.is_authenticated():
        if not view.request.user.is_staff:
            messages.warning(s.request, 'Unable to comply, your account is not allowed to use this tool.')
            return False
    return True


def no_user(view):
    """
    Require:
        no user logged in

    view = `self` of view object that called this function
    """
    if view.request.user.is_authenticated():
        return False
    return True


def create_account(view, form):
    """
    """
    email = form.cleaned_data['username'].lower()
    passw = form.cleaned_data['password1']
    #
    if User.objects.filter(username=email).count() is not 0:
        raise ValueError('That email already has an account')
    #
    testing = EmailValidator(whitelist=[])
    user_part, domain_part = email.rsplit('@', 1)
    testing(email)
    try:
        gethostbyname(domain_part)
    except:
        raise ValueError('Failed to resolve domain {0}'.format(domain_part))
    #
    if passw in common_passwords:
        raise ValueError('Password too weak.')
    if len(passw) < 8:
        raise ValueError('Password too short; 8 character minimum.')
    if len(passw) > 1024:
        raise ValueError('Password too long; max 1024 characters.')
    #
    form.instance.username = email
    return form
