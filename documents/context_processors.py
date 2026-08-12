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

    user_can_edit = False
    try:
        if hasattr(request.user, 'profile'):
            user_can_edit = request.user.profile.role in ['ADMIN', 'REGISTRAR']
    except Exception:
        pass
    if request.user.is_staff or request.user.is_superuser:
        user_can_edit = True

    return {
        'unread_notifications': unread_notifications,
        'overdue_count':        overdue_count,
        'urgent_count':         urgent_count,
        'today_count':          today_count,
        'user_can_edit':        user_can_edit,
    }
