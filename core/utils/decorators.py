from django.http import Http404
from functools import wraps
from django.shortcuts import redirect


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if user.is_authenticated:
                if user.user_type == 'admin':
                    return redirect('/admin/')

                if user.user_type == 'teacher' and not request.path.startswith('/teacher/'):
                    return redirect('/teacher/')

                if user.user_type in allowed_roles:
                    return view_func(request, *args, **kwargs)

            raise Http404('Бет табылмады')

        return _wrapped_view
    return decorator