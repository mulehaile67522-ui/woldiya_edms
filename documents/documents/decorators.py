from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def registrar_required(view_func):
    """Allow only ADMIN and REGISTRAR roles to create/edit/delete."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        try:
            if request.user.profile.role in ('ADMIN', 'REGISTRAR'):
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, 'ይህን ተግባር ለማከናወን ፈቃድ የለዎትም።')
        return redirect('dashboard')
    return wrapper
