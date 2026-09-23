from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def _get_role(user):
    """Return user role string safely."""
    if user.is_superuser or user.is_staff:
        return 'ADMIN'
    try:
        return user.profile.role
    except Exception:
        return 'VIEWER'


def admin_required(view_func):
    """Only ADMIN (superuser/staff or role=ADMIN) can access."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if _get_role(request.user) == 'ADMIN':
            return view_func(request, *args, **kwargs)
        messages.error(request, 'ይህን ተግባር ለማከናወን የአስተዳዳሪ ፈቃድ ያስፈልጋል።')
        return redirect('dashboard')
    return wrapper


def registrar_required(view_func):
    """Only ADMIN and REGISTRAR can create documents."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        role = _get_role(request.user)
        if role in ('ADMIN', 'REGISTRAR'):
            return view_func(request, *args, **kwargs)
        messages.error(request, 'ይህን ተግባር ለማከናወን ፈቃድ የለዎትም። ለአስተዳዳሪ ያሳውቁ።')
        return redirect('dashboard')
    return wrapper


def viewer_required(view_func):
    """Any logged-in user can view — just needs authentication."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
