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

    # ── Role detection ─────────────────────────────────────────────
    user_role = 'VIEWER'
    if request.user.is_superuser or request.user.is_staff:
        user_role = 'ADMIN'
    else:
        try:
            user_role = request.user.profile.role
        except Exception:
            user_role = 'VIEWER'

    # ── Permission levels ──────────────────────────────────────────
    # Admin levels (see all, manage system)
    user_is_admin    = user_role in ('ADMIN', 'MAYOR', 'VICE_MAYOR')

    # Can create/register documents
    user_can_create  = user_role in ('ADMIN', 'MAYOR', 'VICE_MAYOR', 'DEPT_HEAD',
                                      'TEAM_LEAD', 'REGISTRAR', 'EXPERT', 'SUBCITY')

    # Can edit documents
    user_can_edit    = user_role in ('ADMIN', 'MAYOR', 'VICE_MAYOR', 'DEPT_HEAD')

    # Can approve documents
    user_can_approve = user_role in ('MAYOR', 'VICE_MAYOR', 'DEPT_HEAD', 'TEAM_LEAD')

    # Sees all documents (city-wide)
    user_sees_all    = user_role in ('ADMIN', 'MAYOR', 'VICE_MAYOR')

    # Auditor — read-only audit trail
    user_is_auditor  = user_role == 'AUDITOR'

    # Is registrar level
    user_is_registrar = user_role in ('ADMIN', 'MAYOR', 'VICE_MAYOR', 'DEPT_HEAD',
                                       'TEAM_LEAD', 'REGISTRAR', 'EXPERT', 'SUBCITY')

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
        'user_can_approve':     user_can_approve,
        'user_sees_all':        user_sees_all,
        'user_is_auditor':      user_is_auditor,
    }
