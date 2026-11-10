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
    """Only ADMIN can access."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if _get_role(request.user) in ('ADMIN',) or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        messages.error(request, 'ይህን ተግባር ለማከናወን የአስተዳዳሪ ፈቃድ ያስፈልጋል።')
        return redirect('dashboard')
    return wrapper


def registrar_required(view_func):
    """Users who can create/register documents."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if _get_role(request.user) in (
            'ADMIN', 'MAYOR', 'VICE_MAYOR', 'DEPT_HEAD',
            'TEAM_LEAD', 'REGISTRAR', 'EXPERT', 'SUBCITY'
        ):
            return view_func(request, *args, **kwargs)
        messages.error(request, 'ፈቃድ የለዎትም። ለአስተዳዳሪ ያሳውቁ።')
        return redirect('dashboard')
    return wrapper


def dept_head_required(view_func):
    """Only DEPT_HEAD, TEAM_LEAD and above can access."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if _get_role(request.user) in (
            'ADMIN', 'MAYOR', 'VICE_MAYOR', 'DEPT_HEAD', 'TEAM_LEAD'
        ):
            return view_func(request, *args, **kwargs)
        messages.error(request, 'ይህን ተግባር ለማከናወን ቢሮ ኃላፊ ፈቃድ ያስፈልጋል።')
        return redirect('dashboard')
    return wrapper


def viewer_required(view_func):
    """Any logged-in user can access (but auditor is read-only)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
