from django.utils import timezone
from .models import Document


def notifications(request):
    """
    Inject global stats into every template so the sidebar
    always shows live counts without repeating logic in every view.
    Also exposes user_can_edit so templates don't need per-view logic.
    """
    if not request.user.is_authenticated:
        return {}

    today = timezone.localdate()

    unread_notifications = request.user.notifications.filter(is_read=False).count()
    overdue_count = Document.objects.filter(
        due_date__lt=today
    ).exclude(status__in=['COMPLETED', 'ARCHIVED']).count()
    urgent_count = Document.objects.filter(priority='URGENT').exclude(
        status__in=['COMPLETED', 'ARCHIVED']
    ).count()
    today_count = Document.objects.filter(created_at__date=today).count()

    # Role-based edit permission — available in every template
    user_can_edit = False
    if hasattr(request.user, 'profile'):
        user_can_edit = request.user.profile.can_edit()
    elif request.user.is_staff or request.user.is_superuser:
        user_can_edit = True

    return {
        'unread_notifications': unread_notifications,
        'overdue_count':        overdue_count,
        'urgent_count':         urgent_count,
        'today_count':          today_count,
        'user_can_edit':        user_can_edit,
    }
