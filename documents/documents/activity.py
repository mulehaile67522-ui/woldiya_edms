from .models import ActivityLog, Notification
from django.contrib.auth.models import User


def log_activity(document, user, action, detail=''):
    ActivityLog.objects.create(
        document=document,
        user=user,
        action=action,
        detail=detail,
    )


def notify_users(message, link='', exclude_user=None):
    """
    Send in-app notification only to staff/admin/registrar users.
    Avoids spamming viewers with every document change.
    """
    qs = User.objects.filter(is_active=True).filter(
        models_Q=None  # handled below
    )
    # Only notify admins, staff, and registrars
    from django.db.models import Q
    qs = User.objects.filter(is_active=True).filter(
        Q(is_staff=True) | Q(is_superuser=True) | Q(profile__role__in=['ADMIN', 'REGISTRAR'])
    )
    if exclude_user:
        qs = qs.exclude(pk=exclude_user.pk)

    notifications = [
        Notification(user=u, message=message, link=link)
        for u in qs.distinct()
    ]
    if notifications:
        Notification.objects.bulk_create(notifications, ignore_conflicts=True)
