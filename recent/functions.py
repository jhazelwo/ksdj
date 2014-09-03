# recent/functions.py

from .models import Log

def log_form_valid(s, form):
    """
    This is the start of my attempt to
    write a semi-universally-compliant
    logging system
    """
    #
    # 
    try:
        user_name = s.request.user
    except AttributeError:
        user_name = ''
    except Exception as e:
        user_name = e
    #
    # I don't think these should ever
    # actually fail, but if they do
    # then log it. 
    try:
        model_name = s.model.__name__
    except Exception as e:
        model_name = e
    try:
        view_name = s.__class__.__name__
    except Exception as e:
        view_name = e
    #
    #
    # Get object's name and its database ID
    # new  = 'hostname'
    # edit = 'hostname[id]'
    try:
        object_name = s.object.name
    except Exception:
        try:
            object_name = s.request.POST.get('name').lower()
        except Exception as e:
            object_name = e
    try:
        dbid = '[{}]'.format(s.object.id) # Getting Real 
        #dbid = '[' + s.object.id + ']'   # Tired of 
        #dbid = '[%s]' % s.object.id      # Your Sht 
    except AttributeError:
        dbid = ''
    #
    # 
    try:
        post = s.request.POST
    except Exception as e:
        post = e
    #
    #
    D_B = Log(
        user_name=user_name,
        view_name=view_name,
        model_name=model_name,
        object_name=object_name,
        verbose=post,
        )
    D_B.save()
