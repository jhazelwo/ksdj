# recent/functions.py

from .models import Log


def log_form_valid(view):
    """
    Log a successful object change (create|update|delete).
    Should be called from an override of form_valid() or delete()

    view = `self` of a view object. Can be any django.views.generic based view.

    # Example:
    def form_valid(self, form):
        log_form_valid(self)
        messages.success(self.request, 'Changes saved!')
        return super(ObjectChangeView, self).form_valid(form)

    """
    #
    # 
    try:
        user_name = view.request.user
    except AttributeError:
        user_name = ''
    except Exception as e:
        user_name = e
    #
    model_name = False
    if hasattr(view, 'model'):
        model_name = view.model.__name__
    #
    object_name = False
    post = False
    if hasattr(view, 'request'):
        #
        #
        post = view.request.POST
        object_name = post.get('name')
    #
    if hasattr(view, 'object'):
        if hasattr(view.object, 'name'):
            #
            # ObjectCreateView
            object_name = view.object.name
        if hasattr(view.object, 'id'):
            #
            # ObjectUpdateView
            object_name = '{0}[{1}]'.format(view.object.name, view.object.id)
    if hasattr(view, 'old'):
        #
        # ObjectDeleteView
        object_name = '{0}[{1}]'.format(view.old.name, view.old.id)
    #
    this = Log(
        user_name=user_name,
        view_name=view.__class__.__name__,
        model_name=model_name,
        object_name=object_name,
        verbose=post,
        )
    this.save()
