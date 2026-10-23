from django.utils import timezone
from .models import Document, DocumentForward, Category


def notifications(request):
    if not request.user.is_authenticated:
        return {}

    today    = timezone.localdate()
    is_admin = request.user.is_superuser or request.user.is_staff

    try:
        unread_notifications = request.user.notifications.filter(is_read=False).count()
    except Exception:
        unread_notifications = 0

    try:
        inbox_unread = DocumentForward.objects.filter(
            to_user=request.user, is_read=False
        ).count()
    except Exception:
        inbox_unread = 0

    # Scope counts by department for non-admins
    docs = Document.objects.all()
    if not is_admin:
        try:
            role      = request.user.profile.role
            user_dept = request.user.profile.department.strip()
        except Exception:
            role = 'VIEWER'; user_dept = ''
        if role != 'ADMIN':
            if user_dept:
                docs = docs.filter(department=user_dept)
            else:
                docs = docs.filter(created_by=request.user)

    overdue_count = docs.filter(
        due_date__lt=today
    ).exclude(status__in=['COMPLETED', 'ARCHIVED']).count()

    urgent_count = docs.filter(
        priority='URGENT'
    ).exclude(status__in=['COMPLETED', 'ARCHIVED']).count()

    today_count = docs.filter(created_at__date=today).count()

    user_role = 'VIEWER'
    if request.user.is_superuser or request.user.is_staff:
        user_role = 'ADMIN'
    else:
        try:
            user_role = request.user.profile.role
        except Exception:
            user_role = 'VIEWER'

    user_is_admin     = user_role == 'ADMIN'
    user_is_registrar = user_role in ('ADMIN', 'REGISTRAR')
    user_can_edit     = user_is_registrar
    user_can_create   = user_is_registrar

    return {
        'unread_notifications': unread_notifications,
        'inbox_unread':         inbox_unread,
        'overdue_count':        overdue_count,
        'urgent_count':         urgent_count,
        'today_count':          today_count,
        'user_role':            user_role,
        'user_is_admin':        user_is_admin,
        'user_is_registrar':    user_is_registrar,
        'user_can_edit':        user_can_edit,
        'user_can_create':      user_can_create,
        'sidebar_categories':   list(Category.objects.order_by('name')[:8]),
    }
