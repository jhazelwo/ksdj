# human/authtools.py

from django.contrib import messages

# Once again, we should NOT be storing user passwords
# but since I have to, I guess this is the next phase
# This is the top 100 most common passwords from the
# recent Adobe breach.
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
