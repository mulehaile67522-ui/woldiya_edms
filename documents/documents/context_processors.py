from django.utils import timezone
from .models import Document


def notifications(request):
    if not request.user.is_authenticated:
        return {}

    today = timezone.localdate()

    try:
        unread_notifications = request.user.notifications.filter(is_read=False).count()
    except Exception:
        unread_notifications = 0

    overdue_count = Document.objects.filter(
        due_date__lt=today
    ).exclude(status__in=['COMPLETED', 'ARCHIVED']).count()

    urgent_count = Document.objects.filter(
        priority='URGENT'
    ).exclude(status__in=['COMPLETED', 'ARCHIVED']).count()

    today_count = Document.objects.filter(created_at__date=today).count()

    # ── Role detection ────────────────────────────────────────────────
    user_role = 'VIEWER'
    if request.user.is_superuser or request.user.is_staff:
        user_role = 'ADMIN'
    else:
        try:
            user_role = request.user.profile.role
        except Exception:
            user_role = 'VIEWER'

    user_is_admin      = user_role == 'ADMIN'
    user_is_registrar  = user_role in ('ADMIN', 'REGISTRAR')
    user_can_edit      = user_is_admin        # Only ADMIN can edit/delete
    user_can_create    = user_is_registrar    # ADMIN + REGISTRAR can create

    return {
        'unread_notifications': unread_notifications,
        'overdue_count':        overdue_count,
        'urgent_count':         urgent_count,
        'today_count':          today_count,
        'user_role':            user_role,
        'user_is_admin':        user_is_admin,
        'user_is_registrar':    user_is_registrar,
        'user_can_edit':        user_can_edit,
        'user_can_create':      user_can_create,
    }
