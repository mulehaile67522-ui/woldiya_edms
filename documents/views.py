from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count, F
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.conf import settings
import json, datetime, csv, os

from .models import (Document, Category, Notification,
                     InnovationProject, Training, UserProfile, ActivityLog)
from .forms import DocumentForm, DocumentSearchForm, CategoryForm, InnovationProjectForm, TrainingForm
from .activity import log_activity, notify_users
from .decorators import registrar_required, admin_required
from .utils import generate_reference_number, generate_qr_code


def _get_client_ip(request):
    """Get real IP address from request."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _is_locked_out(username, ip):
    """Return True if this username or IP has too many recent failed attempts."""
    from .models import LoginAttempt
    import datetime as _dt
    window = timezone.now() - _dt.timedelta(minutes=15)
    failed = LoginAttempt.objects.filter(
        success=False,
        timestamp__gte=window,
    ).filter(
        Q(username__iexact=username) | Q(ip_address=ip)
    ).count()
    return failed >= 5


# ──────────────────────────── AUTH ───────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    ip         = _get_client_ip(request)
    error_msg  = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # ── Check lockout ─────────────────────────────────────────
        if _is_locked_out(username, ip):
            error_msg = 'በጣም ብዙ ጊዜ ሞክረዋል። 15 ደቂቃ ጠብቁ።'
            from .models import LoginAttempt
            LoginAttempt.objects.create(
                username=username, ip_address=ip, success=False,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:300]
            )
        else:
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                # Log success
                from .models import LoginAttempt
                LoginAttempt.objects.create(
                    username=username, ip_address=ip, success=True,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:300]
                )
                messages.success(request, f'እንኳን ደህና መጡ, {user.get_full_name() or user.username}!')
                return redirect(request.GET.get('next', 'dashboard'))
            else:
                # Log failure
                from .models import LoginAttempt
                LoginAttempt.objects.create(
                    username=username, ip_address=ip, success=False,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:300]
                )
                # Count remaining attempts
                import datetime as _dt
                window = timezone.now() - _dt.timedelta(minutes=15)
                failed = LoginAttempt.objects.filter(
                    success=False, timestamp__gte=window,
                    username__iexact=username
                ).count()
                remaining = max(0, 5 - failed)
                if remaining > 0:
                    error_msg = f'ስህተት! {remaining} ጊዜ ብቻ ቀርቷል።'
                else:
                    error_msg = 'Account ተቆልፏል። 15 ደቂቃ ጠብቁ።'
    else:
        form = AuthenticationForm(request)

    return render(request, 'documents/login.html', {
        'form': AuthenticationForm(request),
        'error_msg': error_msg,
    })


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    else:
        logout(request)  # allow GET too for backward compatibility
    return redirect('login')


# ──────────────────────────── DASHBOARD ──────────────────────────────

@login_required
def dashboard(request):
    today      = timezone.localdate()
    week_start = today - datetime.timedelta(days=today.weekday())
    docs       = Document.objects.all()

    # ── Department-based access control ──────────────────────────────
    is_admin = request.user.is_superuser or request.user.is_staff
    if not is_admin:
        try:
            role      = request.user.profile.role
            user_dept = request.user.profile.department.strip()
        except Exception:
            role      = 'VIEWER'
            user_dept = ''

        # ── Least Privilege: filter docs by role ─────────────────────
        from .models import DocumentForward
        from django.db.models import Q
        fwd_ids      = list(DocumentForward.objects.filter(to_user=request.user).values_list('document_id', flat=True))
        assigned_ids = list(docs.filter(assigned_to=request.user).values_list('pk', flat=True))

        if role == 'ADMIN':
            pass  # IT admin sees all for system support
        elif role in ('MAYOR', 'VICE_MAYOR'):
            # Executive: only Mayor office docs + forwarded/assigned to them
            docs = docs.filter(
                Q(department='ከንቲባ ጽፈት ቤት') |
                Q(receiver__icontains='ከንቲባ') |
                Q(pk__in=fwd_ids) |
                Q(pk__in=assigned_ids)
            )
        elif role == 'DEPT_HEAD':
            if user_dept:
                docs = docs.filter(Q(department=user_dept) | Q(pk__in=fwd_ids) | Q(pk__in=assigned_ids))
        elif role in ('REGISTRAR', 'SUBCITY'):
            if user_dept:
                docs = docs.filter(Q(department=user_dept) | Q(pk__in=fwd_ids) | Q(pk__in=assigned_ids))
        elif role == 'VIEWER':
            docs = docs.filter(Q(pk__in=fwd_ids) | Q(pk__in=assigned_ids))
        else:
            docs = docs.filter(created_by=request.user)

    total       = docs.count()
    incoming    = docs.filter(doc_type='INCOMING').count()
    outgoing    = docs.filter(doc_type='OUTGOING').count()
    internal    = docs.filter(doc_type='INTERNAL').count()
    pending     = docs.filter(status='PENDING').count()
    in_progress = docs.filter(status='IN_PROGRESS').count()
    completed   = docs.filter(status='COMPLETED').count()
    urgent      = docs.filter(priority='URGENT').count()
    overdue     = docs.filter(due_date__lt=today).exclude(
                    status__in=['COMPLETED', 'ARCHIVED']).count()
    today_docs  = docs.filter(created_at__date=today).count()
    week_docs   = docs.filter(created_at__date__gte=week_start).count()
    my_docs     = docs.filter(assigned_to=request.user).exclude(
                    status__in=['COMPLETED', 'ARCHIVED']).count()

    recent_docs   = docs.select_related('category', 'created_by').order_by('-created_at')[:8]
    deadline_soon = docs.filter(
        due_date__gte=today,
        due_date__lte=today + datetime.timedelta(days=7)
    ).exclude(status__in=['COMPLETED', 'ARCHIVED']).order_by('due_date')[:6]

    chart_labels, chart_data = [], []
    for i in range(5, -1, -1):
        d = today - datetime.timedelta(days=30 * i)
        chart_labels.append(d.strftime('%b %Y'))
        chart_data.append(docs.filter(created_at__year=d.year, created_at__month=d.month).count())

    type_data    = {'ገቢ ደብዳቤ': incoming, 'ወጪ ደብዳቤ': outgoing, 'የ ማስታወሻ': internal}
    status_labels = [s[1] for s in Document.STATUS_CHOICES]
    status_values = [docs.filter(status=s[0]).count() for s in Document.STATUS_CHOICES]

    return render(request, 'documents/dashboard.html', {
        'total': total, 'incoming': incoming, 'outgoing': outgoing, 'internal': internal,
        'pending': pending, 'in_progress': in_progress, 'completed': completed,
        'urgent': urgent, 'overdue': overdue,
        'today_docs': today_docs, 'week_docs': week_docs, 'my_docs': my_docs,
        'recent_docs': recent_docs, 'deadline_soon': deadline_soon,
        'chart_labels':  json.dumps(chart_labels),
        'chart_data':    json.dumps(chart_data),
        'type_labels':   json.dumps(list(type_data.keys())),
        'type_values':   json.dumps(list(type_data.values())),
        'status_labels': json.dumps(status_labels),
        'status_values': json.dumps(status_values),
        'today': today,
        'completion_pct': int((completed / total * 100) if total else 0),
    })


# ──────────────────────────── DOCUMENT LIST ──────────────────────────

@login_required
def document_list(request):
    form = DocumentSearchForm(request.GET or None)
    docs = Document.objects.select_related('category', 'created_by').all()

    # ── Department-based access control ──────────────────────────────
    # Admin sees all. Others see only their department's documents.
    is_admin = request.user.is_superuser or request.user.is_staff
    if not is_admin:
        try:
            role      = request.user.profile.role
            user_dept = request.user.profile.department.strip()
        except Exception:
            role      = 'VIEWER'
            user_dept = ''

        # ── Least Privilege ───────────────────────────────────────────
        from .models import DocumentForward
        from django.db.models import Q as DQ
        fwd_ids      = list(DocumentForward.objects.filter(to_user=request.user).values_list('document_id', flat=True))
        assigned_ids = list(docs.filter(assigned_to=request.user).values_list('pk', flat=True))
        if role == 'ADMIN':
            pass
        elif role in ('MAYOR', 'VICE_MAYOR'):
            docs = docs.filter(DQ(department='ከንቲባ ጽፈት ቤት') | DQ(receiver__icontains='ከንቲባ') | DQ(pk__in=fwd_ids) | DQ(pk__in=assigned_ids))
        elif role in ('DEPT_HEAD', 'REGISTRAR', 'SUBCITY'):
            if user_dept:
                docs = docs.filter(DQ(department=user_dept) | DQ(pk__in=fwd_ids) | DQ(pk__in=assigned_ids))
        elif role == 'VIEWER':
            docs = docs.filter(DQ(pk__in=fwd_ids) | DQ(pk__in=assigned_ids))
        else:
            docs = docs.filter(created_by=request.user)

    if form.is_valid():
        q = form.cleaned_data.get('query')
        if q:
            docs = docs.filter(
                Q(title__icontains=q) | Q(reference_number__icontains=q) |
                Q(sender__icontains=q) | Q(receiver__icontains=q) |
                Q(description__icontains=q)
            )
        for field in ('doc_type', 'status', 'priority', 'category'):
            val = form.cleaned_data.get(field)
            if val:
                docs = docs.filter(**{field: val})
        if form.cleaned_data.get('date_from'):
            docs = docs.filter(created_at__date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            docs = docs.filter(created_at__date__lte=form.cleaned_data['date_to'])

    if request.GET.get('export') == 'csv':
        return _export_csv(docs)

    # Sorting
    sort = request.GET.get('sort', '-created_at')
    allowed_sorts = ['reference_number', '-reference_number', 'created_at', '-created_at',
                     'due_date', '-due_date', 'title', '-title']
    if sort not in allowed_sorts:
        sort = '-created_at'
    docs = docs.order_by(sort)

    paginator = Paginator(docs, 15)
    page_obj  = paginator.get_page(request.GET.get('page'))
    today     = timezone.localdate()
    return render(request, 'documents/document_list.html', {
        'form': form, 'page_obj': page_obj,
        'total_results': paginator.count,
        'today_date': today,
        'today_plus7': today + datetime.timedelta(days=7),
    })


def _export_csv(queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="documents.csv"'
    response.write('\ufeff')
    w = csv.writer(response)
    w.writerow(['ቁጥር', 'ርዕስ', 'ዓይነት', 'ሁኔታ', 'ቅድሚያ', 'ላኪ', 'ተቀባይ', 'ቀን'])
    for d in queryset:
        w.writerow([
            d.reference_number, d.title, d.get_doc_type_display(),
            d.get_status_display(), d.get_priority_display(),
            d.sender, d.receiver, d.created_at.strftime('%d/%m/%Y'),
        ])
    return response


# ──────────────────────────── DOCUMENT DETAIL ────────────────────────

@login_required
def document_detail(request, pk):
    doc        = get_object_or_404(Document, pk=pk)

    # ── Department-based access control ──────────────────────────────
    is_admin = request.user.is_superuser or request.user.is_staff
    if not is_admin:
        try:
            role      = request.user.profile.role
            user_dept = request.user.profile.department.strip()
        except Exception:
            role      = 'VIEWER'
            user_dept = ''

        # MAYOR and VICE_MAYOR see ALL documents
        sees_all = role in ('MAYOR', 'VICE_MAYOR', 'ADMIN')

        # Check if document was forwarded to this user
        was_forwarded = False
        try:
            from .models import DocumentForward
            was_forwarded = DocumentForward.objects.filter(
                document=doc, to_user=request.user
            ).exists()
        except Exception:
            pass

        if not sees_all and not was_forwarded:
            if user_dept and doc.department and doc.department != user_dept:
                messages.error(request, 'ይህን ደብዳቤ የማየት ፈቃድ የለዎትም።')
                return redirect('document_list')

    activities = doc.activities.select_related('user').order_by('-timestamp')[:20]
    today      = timezone.localdate()
    is_overdue = (doc.due_date and doc.due_date < today
                  and doc.status not in ['COMPLETED', 'ARCHIVED'])
    Document.objects.filter(pk=pk).update(view_count=F('view_count') + 1)
    return render(request, 'documents/document_detail.html', {
        'doc': doc, 'activities': activities, 'is_overdue': is_overdue,
    })


# ──────────────────────────── CREATE ─────────────────────────────────

@login_required
@registrar_required
def document_create(request):
    form = DocumentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.created_by = request.user
        # Auto-assign department from user profile
        if not doc.department:
            try:
                doc.department = request.user.profile.department.strip()
            except Exception:
                doc.department = ''
        doc.save()
        log_activity(doc, request.user, 'ደብዳቤ ተመዝግቧል', f'"{doc.title}" ተመዝግቧል።')
        notify_users(
            f'አዲስ ደብዳቤ "{doc.reference_number} — {doc.title}" ተመዝግቧል።',
            link=f'/documents/{doc.pk}/', exclude_user=request.user,
        )
        messages.success(request, f'ደብዳቤ "{doc.title}" ተመዝግቧል!')
        return redirect('document_detail', pk=doc.pk)
    return render(request, 'documents/document_form.html', {'form': form, 'action': 'ምዝገባ'})


# ──────────────────────────── UPDATE ─────────────────────────────────

@login_required
@registrar_required
def document_update(request, pk):
    doc        = get_object_or_404(Document, pk=pk)
    old_status = doc.status
    form       = DocumentForm(request.POST or None, request.FILES or None, instance=doc)
    if request.method == 'POST' and form.is_valid():
        updated = form.save()
        if old_status != updated.status:
            log_activity(doc, request.user, 'ሁኔታ ተቀይሯል',
                         f'"{doc.get_status_display()}" → "{updated.get_status_display()}"')
        else:
            log_activity(doc, request.user, 'ደብዳቤ ተዘምኗል')
        messages.success(request, 'ደብዳቤ ተዘምኗል!')
        return redirect('document_detail', pk=doc.pk)
    return render(request, 'documents/document_form.html', {
        'form': form, 'doc': doc, 'action': 'ማስተካከያ'
    })


# ──────────────────────────── DELETE ─────────────────────────────────

@login_required
@admin_required
def document_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        title  = doc.title
        ref    = doc.reference_number
        reason = request.POST.get('reason', '').strip()
        # Save deletion record BEFORE deleting
        from .models import DeletionLog
        DeletionLog.objects.create(
            reference_number = ref,
            title            = title,
            doc_type         = doc.doc_type,
            department       = doc.department,
            deleted_by       = request.user,
            reason           = reason,
        )
        doc.delete()
        messages.warning(request, f'Document "{title}" ({ref}) deleted.')
        return redirect('document_list')
    return render(request, 'documents/document_confirm_delete.html', {'doc': doc})


# ──────────────────────────── QUICK STATUS ───────────────────────────

@login_required
@admin_required
@require_POST
def update_status(request, pk):
    doc        = get_object_or_404(Document, pk=pk)
    new_status = request.POST.get('status')
    valid      = [s[0] for s in Document.STATUS_CHOICES]
    if new_status in valid:
        old = doc.get_status_display()
        doc.status = new_status
        doc.save(update_fields=['status', 'updated_at'])
        log_activity(doc, request.user, 'ሁኔታ ተቀይሯል',
                     f'"{old}" → "{doc.get_status_display()}"')
        return JsonResponse({'success': True, 'new_status': doc.get_status_display()})
    return JsonResponse({'success': False}, status=400)


# ──────────────────────────── DOWNLOAD ───────────────────────────────

@login_required
def document_download(request, pk):
    from django.http import FileResponse, Http404
    doc = get_object_or_404(Document, pk=pk)
    if not doc.file:
        messages.error(request, 'ፋይሉ አልተገኘም።')
        return redirect('document_detail', pk=pk)
    try:
        file_path = doc.file.path
        if not os.path.exists(file_path):
            raise Http404
        Document.objects.filter(pk=pk).update(download_count=F('download_count') + 1)
        log_activity(doc, request.user, 'ፋይል ወረደ',
                     f'"{os.path.basename(file_path)}" ወረደ።')
        response = FileResponse(open(file_path, 'rb'), as_attachment=True)
        response['Content-Disposition'] = (
            f'attachment; filename="{os.path.basename(file_path)}"'
        )
        return response
    except Exception:
        messages.error(request, 'ፋይሉ ከሰርቨሩ ላይ አልተገኘም።')
        return redirect('document_detail', pk=pk)


# ──────────────────────────── PRINT & QR ─────────────────────────────

@login_required
def document_print(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    return render(request, 'documents/document_print.html', {'doc': doc})


@login_required
def document_qr(request, pk):
    """Return the QR code PNG — with Woldiya logo embedded in the centre."""
    doc      = get_object_or_404(Document, pk=pk)
    scheme   = 'https' if request.is_secure() else 'http'
    doc_url  = f"{scheme}://{request.get_host()}/documents/{doc.pk}/"
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'woldiya_logo.png')
    png_bytes = generate_qr_code(doc_url, logo_path=logo_path)
    return HttpResponse(png_bytes, content_type='image/png')


# ──────────────────────────── OVERDUE ────────────────────────────────

@login_required
def overdue_documents(request):
    today = timezone.localdate()
    docs  = Document.objects.filter(due_date__lt=today).exclude(
                status__in=['COMPLETED', 'ARCHIVED']).order_by('due_date')
    # Department scoping
    is_admin = request.user.is_superuser or request.user.is_staff
    if not is_admin:
        try:
            role      = request.user.profile.role
            user_dept = request.user.profile.department.strip()
        except Exception:
            role = 'VIEWER'; user_dept = ''
        from .models import DocumentForward
        from django.db.models import Q as DQ
        fwd_ids = list(DocumentForward.objects.filter(to_user=request.user).values_list('document_id', flat=True))
        if role == 'ADMIN':
            pass
        elif role in ('MAYOR', 'VICE_MAYOR'):
            docs = docs.filter(DQ(department='ከንቲባ ጽፈት ቤት') | DQ(pk__in=fwd_ids))
        elif role in ('DEPT_HEAD', 'REGISTRAR', 'SUBCITY'):
            if user_dept:
                docs = docs.filter(DQ(department=user_dept) | DQ(pk__in=fwd_ids))
        elif role == 'VIEWER':
            docs = docs.filter(pk__in=fwd_ids)
        else:
            docs = docs.filter(created_by=request.user)
    return render(request, 'documents/overdue.html', {'docs': docs, 'today': today})


# ──────────────────────────── NOTIFICATIONS ──────────────────────────

@login_required
def notifications_view(request):
    # Mark all as read on visit
    if request.GET.get('mark_all'):
        request.user.notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, 'ሁሉም ማሳወቂያዎች ተነቡ።')
        return redirect('notifications')

    notifs = request.user.notifications.order_by('-created_at')[:100]
    # Group by date
    from itertools import groupby
    from django.utils.timezone import localdate
    grouped = {}
    for n in notifs:
        day = localdate(n.created_at)
        grouped.setdefault(day, []).append(n)

    return render(request, 'documents/notifications.html', {
        'notifs': notifs,
        'grouped': grouped,
        'unread_count': request.user.notifications.filter(is_read=False).count(),
        'today': timezone.localdate(),
    })


@login_required
@require_POST
def mark_notification_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True
    n.save(update_fields=['is_read'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect(n.link or 'notifications')


@login_required
@require_POST
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, 'ሁሉም ማሳወቂያዎች ተነቡ።')
    return redirect('notifications')


# ──────────────────────────── AUDIT TRAIL ────────────────────────────

@login_required
@admin_required
def audit_trail(request):
    logs = ActivityLog.objects.select_related('document', 'user').order_by('-timestamp')

    # Filters
    user_q   = request.GET.get('user', '').strip()
    action_q = request.GET.get('action', '').strip()
    date_f   = request.GET.get('date_from', '').strip()
    date_t   = request.GET.get('date_to', '').strip()

    if user_q:
        logs = logs.filter(
            Q(user__username__icontains=user_q) |
            Q(user__first_name__icontains=user_q) |
            Q(user__last_name__icontains=user_q)
        )
    if action_q:
        logs = logs.filter(action__icontains=action_q)
    if date_f:
        try:
            logs = logs.filter(timestamp__date__gte=datetime.date.fromisoformat(date_f))
        except ValueError:
            pass
    if date_t:
        try:
            logs = logs.filter(timestamp__date__lte=datetime.date.fromisoformat(date_t))
        except ValueError:
            pass

    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="audit_trail.csv"'
        response.write('\ufeff')
        w = csv.writer(response)
        w.writerow(['ቀን', 'ተጠቃሚ', 'ደብዳቤ', 'እርምጃ', 'ዝርዝር'])
        for log in logs:
            w.writerow([
                log.timestamp.strftime('%d/%m/%Y %H:%M'),
                log.user.get_full_name() or log.user.username if log.user else '—',
                log.document.reference_number,
                log.action,
                log.detail or '—',
            ])
        return response

    paginator = Paginator(logs, 30)
    page_obj  = paginator.get_page(request.GET.get('page'))
    users     = User.objects.filter(is_active=True).order_by('username')
    # Include deletion logs
    from .models import DeletionLog
    deletion_logs = DeletionLog.objects.select_related('deleted_by').order_by('-deleted_at')[:50]
    return render(request, 'documents/audit_trail.html', {
        'page_obj': page_obj, 'users': users,
        'filter_user': user_q, 'filter_action': action_q,
        'filter_date_from': date_f, 'filter_date_to': date_t,
        'deletion_logs': deletion_logs,
    })


# ──────────────────────────── REPORTS ────────────────────────────────

@login_required
@admin_required
def reports(request):
    today = timezone.localdate()
    docs  = Document.objects.all()

    by_type     = {t: docs.filter(doc_type=t).count() for t, _ in Document.DOCUMENT_TYPES}
    by_status   = {s: docs.filter(status=s).count()   for s, _ in Document.STATUS_CHOICES}
    by_priority = {p: docs.filter(priority=p).count() for p, _ in Document.PRIORITY_CHOICES}
    by_category = Category.objects.annotate(cnt=Count('documents')).order_by('-cnt')

    monthly = []
    for i in range(11, -1, -1):
        d = today.replace(day=1) - datetime.timedelta(days=30 * i)
        monthly.append({
            'label': d.strftime('%b %Y'),
            'count': docs.filter(created_at__year=d.year, created_at__month=d.month).count(),
        })

    if request.GET.get('export') == 'excel':
        return _export_excel_report(docs, by_type, by_status, by_priority, monthly, today)
    if request.GET.get('export') == 'pdf':
        return _export_pdf_report(docs, by_type, by_status, by_priority, monthly, today)

    return render(request, 'documents/reports.html', {
        'total': docs.count(),
        'by_type': by_type, 'by_status': by_status,
        'by_priority': by_priority, 'by_category': by_category,
        'monthly': monthly, 'today': today,
    })


def _export_excel_report(docs, by_type, by_status, by_priority, monthly, today):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
    except ImportError:
        return HttpResponse('openpyxl አልተጫነም። pip install openpyxl', status=500)

    wb = openpyxl.Workbook()
    hdr_font  = Font(bold=True, color='FFFFFF')
    hdr_fill  = PatternFill('solid', fgColor='1B4F72')
    center    = Alignment(horizontal='center')

    # ── Sheet 1: Summary ──
    ws = wb.active
    ws.title = 'ማጠቃለያ'
    ws.append(['ወልድያ ከተማ አስተዳደር — EDMS ሪፖርት'])
    ws['A1'].font = Font(bold=True, size=14)
    ws.append([f'ዛሬ: {today}'])
    ws.append([])
    ws.append(['ጠቅላላ', 'ዓይነት', 'ብዛት'])
    for cell in ws[4]:
        cell.font = hdr_font; cell.fill = hdr_fill; cell.alignment = center
    ws.append(['ጠቅላላ ደብዳቤ', '', docs.count()])
    for k, v in by_type.items():
        ws.append([k, '', v])
    ws.append([])
    ws.append(['ሁኔታ', '', 'ብዛት'])
    for k, v in by_status.items():
        ws.append([k, '', v])
    ws.column_dimensions['A'].width = 22
    ws.column_dimensions['C'].width = 12

    # ── Sheet 2: Monthly ──
    ws2 = wb.create_sheet('ወርሃዊ')
    ws2.append(['ወር', 'ደብዳቤ ብዛት'])
    for cell in ws2[1]:
        cell.font = hdr_font; cell.fill = hdr_fill
    for row in monthly:
        ws2.append([row['label'], row['count']])
    ws2.column_dimensions['A'].width = 18

    # ── Sheet 3: All documents ──
    ws3 = wb.create_sheet('ሁሉም ደብዳቤዎች')
    ws3.append(['ቁጥር', 'ርዕስ', 'ዓይነት', 'ሁኔታ', 'ቅድሚያ', 'ላኪ', 'ተቀባይ', 'ቀን'])
    for cell in ws3[1]:
        cell.font = hdr_font; cell.fill = hdr_fill
    for d in docs.order_by('-created_at'):
        ws3.append([
            d.reference_number, d.title, d.get_doc_type_display(),
            d.get_status_display(), d.get_priority_display(),
            d.sender, d.receiver, d.created_at.strftime('%d/%m/%Y'),
        ])
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
        ws3.column_dimensions[col].width = 20

    from io import BytesIO
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(
        buf.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="edms_report_{today}.xlsx"'
    return response


def _export_pdf_report(docs, by_type, by_status, by_priority, monthly, today):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable)
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return HttpResponse('reportlab አልተጫነም። pip install reportlab', status=500)

    from io import BytesIO
    buf  = BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=A4,
                              rightMargin=2*cm, leftMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    brand  = colors.HexColor('#1B4F72')
    gold   = colors.HexColor('#C8960C')
    story  = []

    # ── Register Ethiopic font ──
    AM_FONT = 'Helvetica'
    AM_BOLD = 'Helvetica-Bold'
    font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'ethiopic.ttf')
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('Ethiopic', font_path))
            AM_FONT = 'Ethiopic'
            AM_BOLD = 'Ethiopic'
        except Exception:
            pass

    # Title
    title_style = ParagraphStyle('Title', fontName=AM_BOLD,
                                  textColor=brand, fontSize=18, spaceAfter=6)
    story.append(Paragraph('ወልድያ ከተማ አስተዳደር — EDMS ሪፖርት', title_style))
    story.append(Paragraph(f'ዛሬ: {today}', ParagraphStyle('date', fontName=AM_FONT, fontSize=11, spaceAfter=6)))
    story.append(HRFlowable(width='100%', color=gold, thickness=2, spaceAfter=12))

    # Summary table
    summary_data = [['ምድብ', 'ብዛት']]
    summary_data.append(['ጠቅላላ ደብዳቤ', str(docs.count())])
    for k, v in by_type.items():
        summary_data.append([k, str(v)])
    for k, v in by_status.items():
        summary_data.append([k, str(v)])

    t = Table(summary_data, colWidths=[12*cm, 4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), brand),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), AM_BOLD),
        ('FONTNAME',   (0, 1), (-1, -1), AM_FONT),
        ('ALIGN',      (1, 0), (1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F4F8')]),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('PADDING',    (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    # Monthly table
    story.append(Paragraph('ወርሃዊ ምዝገባ', ParagraphStyle('h2', fontName=AM_BOLD, fontSize=14, textColor=brand, spaceAfter=8)))
    month_data = [['ወር', 'ደብዳቤ']]
    for row in monthly:
        month_data.append([row['label'], str(row['count'])])
    t2 = Table(month_data, colWidths=[12*cm, 4*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), brand),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), AM_BOLD),
        ('FONTNAME',   (0, 1), (-1, -1), AM_FONT),
        ('ALIGN',      (1, 0), (1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F4F8')]),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('PADDING',    (0, 0), (-1, -1), 6),
    ]))
    story.append(t2)

    doc.build(story)
    buf.seek(0)
    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="edms_report_{today}.pdf"'
    return response


# ──────────────────────────── CAPACITY BUILDING ──────────────────────

@login_required
def capacity_building(request):
    projects  = InnovationProject.objects.select_related('lead').order_by('-created_at')
    trainings = Training.objects.prefetch_related('participants').order_by('-date')

    proj_form     = InnovationProjectForm()
    training_form = TrainingForm()

    if request.method == 'POST':
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'ፈቃድ የለዎትም።')
            return redirect('capacity_building')

        form_type = request.POST.get('form_type')

        if form_type == 'project':
            proj_form = InnovationProjectForm(request.POST)
            if proj_form.is_valid():
                proj_form.save()
                messages.success(request, 'ፕሮጀክት ተፈጠረ!')
                return redirect('capacity_building')

        elif form_type == 'training':
            training_form = TrainingForm(request.POST)
            if training_form.is_valid():
                training_form.save()
                messages.success(request, 'ሥልጠና ተፈጠረ!')
                return redirect('capacity_building')

    return render(request, 'documents/capacity_building.html', {
        'projects':      projects,
        'trainings':     trainings,
        'proj_form':     proj_form,
        'training_form': training_form,
    })


# ──────────────────────────── USER MANAGEMENT ────────────────────────

@login_required
def user_management(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'ፈቃድ የለዎትም።')
        return redirect('dashboard')
    users = User.objects.select_related('profile').filter(is_active=True).order_by('username')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role    = request.POST.get('role')
        dept    = request.POST.get('department', '').strip()
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            if role in dict(UserProfile.ROLE_CHOICES):
                profile.role       = role
                profile.department = dept
                profile.save()
                messages.success(request, 'ተጠቃሚ ተዘምኗል።')
        except UserProfile.DoesNotExist:
            messages.error(request, 'ተጠቃሚ አልተገኘም።')
        return redirect('user_management')
    return render(request, 'documents/user_management.html', {
        'users': users, 'role_choices': UserProfile.ROLE_CHOICES,
    })


# ──────────────────────────── API HELPERS ────────────────────────────

@login_required
def suggest_reference(request):
    doc_type = request.GET.get('doc_type', 'INCOMING')
    return JsonResponse({'reference': generate_reference_number(doc_type)})


# ──────────────────────────── CATEGORIES ─────────────────────────────

@login_required
def category_list(request):
    cats = Category.objects.annotate(cnt=Count('documents')).order_by('name')
    return render(request, 'documents/category_list.html', {'cats': cats})


@login_required
@registrar_required
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'ምድብ ተፈጠረ!')
        return redirect('category_list')
    return render(request, 'documents/category_form.html', {'form': form, 'action': 'ፍጠር'})


@login_required
@registrar_required
def category_update(request, pk):
    cat  = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'ምድብ ተዘምኗል!')
        return redirect('category_list')
    return render(request, 'documents/category_form.html', {
        'form': form, 'cat': cat, 'action': 'አርትዕ'
    })


@login_required
@registrar_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        cat.delete()
        messages.warning(request, f'ምድብ "{cat}" ተሰርዟል።')
        return redirect('category_list')
    return render(request, 'documents/category_confirm_delete.html', {'cat': cat})


# ──────────────────────────── PROFILE ────────────────────────────────

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        # Update user info
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name  = request.POST.get('last_name', '').strip()
        request.user.email      = request.POST.get('email', '').strip()
        request.user.save(update_fields=['first_name', 'last_name', 'email'])
        # Update profile
        profile.department = request.POST.get('department', '').strip()
        profile.phone      = request.POST.get('phone', '').strip()
        profile.save(update_fields=['department', 'phone'])
        messages.success(request, 'መረጃዎ ተዘምኗል!')
        return redirect('profile')

    my_docs     = Document.objects.filter(created_by=request.user).order_by('-created_at')[:5]
    my_assigned = Document.objects.filter(assigned_to=request.user).exclude(
                    status__in=['COMPLETED','ARCHIVED']).order_by('-created_at')[:5]
    my_total    = Document.objects.filter(created_by=request.user).count()
    return render(request, 'documents/profile.html', {
        'profile':     profile,
        'my_docs':     my_docs,
        'my_assigned': my_assigned,
        'my_total':    my_total,
    })


# ──────────────────────────── MY DOCUMENTS ───────────────────────────

@login_required
def my_documents(request):
    today = timezone.localdate()
    assigned = Document.objects.filter(
        assigned_to=request.user
    ).select_related('category').order_by('-created_at')

    created = Document.objects.filter(
        created_by=request.user
    ).select_related('category').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        assigned = assigned.filter(status=status_filter)
        created  = created.filter(status=status_filter)

    return render(request, 'documents/my_documents.html', {
        'assigned':      assigned[:20],
        'created':       created[:20],
        'assigned_count': assigned.count(),
        'created_count':  created.count(),
        'status_filter':  status_filter,
        'status_choices': Document.STATUS_CHOICES,
        'today':          today,
    })


# ──────────────────────────── WELCOME EMAIL ──────────────────────────

def _send_welcome_email(user, username, password, department, role):
    """Send welcome email to newly created user with login credentials."""
    try:
        from django.core.mail import send_mail
        role_display = {
            'ADMIN': 'Administrator', 'REGISTRAR': 'Registrar', 'VIEWER': 'Viewer',
        }.get(role, role)
        subject = 'Welcome to Woldiya City Administration EDMS'
        message = f"""Dear {user.get_full_name() or username},

Your account has been created on the Woldiya City Administration EDMS.

Login Details:
  Website:    https://muleedms.pythonanywhere.com
  Username:   {username}
  Password:   {password}
  Role:       {role_display}
  Department: {department or 'Not assigned'}

Please login and change your password immediately.

Woldiya City Administration — Innovation & Technology Group
"""
        send_mail(
            subject, message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'edms@woldiya.gov.et'),
            [user.email],
            fail_silently=True,
        )
    except Exception:
        pass


# ──────────────────────────── CREATE USER ────────────────────────────

@login_required
def create_user_view(request):
    """ADMIN-only: create a new user with role and department."""
    from .decorators import _get_role
    if _get_role(request.user) != 'ADMIN':
        messages.error(request, 'ይህን ተግባር ለማከናወን የአስተዳዳሪ ፈቃድ ያስፈልጋል።')
        return redirect('dashboard')

    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        password   = request.POST.get('password', '').strip()
        password2  = request.POST.get('password2', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        role       = request.POST.get('role', 'VIEWER')
        department = request.POST.get('department', '').strip()
        phone      = request.POST.get('phone', '').strip()

        # Validation
        errors = []
        if not username:
            errors.append('Username ያስፈልጋል።')
        elif User.objects.filter(username=username).exists():
            errors.append(f'"{username}" አስቀድሞ ተመዝግቧል።')
        if not password:
            errors.append('Password ያስፈልጋል።')
        elif len(password) < 8:
            errors.append('Password ቢያንስ 8 ፊደላት ይኑሩት።')
        elif password != password2:
            errors.append('Passwords አይዛመዱም።')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'documents/create_user.html', {
                'role_choices': UserProfile.ROLE_CHOICES,
                'post': request.POST,
            })

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role       = role
        profile.department = department
        profile.phone      = phone
        profile.save()

        # Send welcome email if user has email
        if email:
            _send_welcome_email(user, username, password, department, role)

        messages.success(request, f'User "{username}" ({first_name} {last_name}) created!')
        return redirect('user_management')

    return render(request, 'documents/create_user.html', {
        'role_choices': UserProfile.ROLE_CHOICES,
        'post': {},
    })

# ──────────────────────────── DOCUMENT FORWARD ───────────────────────

@login_required
@registrar_required
def document_forward(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    users = User.objects.filter(is_active=True).exclude(pk=request.user.pk).select_related('profile')

    if request.method == 'POST':
        to_user_id   = request.POST.get('to_user')
        to_department = request.POST.get('to_department', '').strip()
        note         = request.POST.get('note', '').strip()

        to_user = None
        if to_user_id:
            try:
                to_user = User.objects.get(pk=to_user_id)
            except User.DoesNotExist:
                pass

        from .models import DocumentForward
        fwd = DocumentForward.objects.create(
            document=doc,
            from_user=request.user,
            to_user=to_user,
            to_department=to_department,
            note=note,
        )

        # Log activity
        dest = to_user.get_full_name() or to_user.username if to_user else to_department
        log_activity(doc, request.user, 'ደብዳቤ ተላልፏል', f'ወደ {dest} ተላልፏል። {note}')

        # Notify recipient
        if to_user:
            Notification.objects.create(
                user=to_user,
                message=f'ደብዳቤ "{doc.reference_number} — {doc.title}" ወደዎ ተላልፏል። ማስታወሻ: {note or "—"}',
                link=f'/documents/{doc.pk}/',
            )
            # Send email if user has email
            if to_user.email:
                _send_forward_email(to_user, doc, request.user, note)

        messages.success(request, f'ደብዳቤ ወደ "{dest}" ተላልፏል!')
        return redirect('document_detail', pk=doc.pk)

    return render(request, 'documents/document_forward.html', {
        'doc': doc, 'users': users,
    })


def _send_forward_email(to_user, doc, from_user, note):
    """Send email notification when a document is forwarded."""
    try:
        from django.core.mail import send_mail
        subject = f'[EDMS] ደብዳቤ ተላልፏል — {doc.reference_number}'
        message = f"""
ሰላም {to_user.get_full_name() or to_user.username}،

{from_user.get_full_name() or from_user.username} ደብዳቤ ወደዎ አስተላልፏል።

ደብዳቤ: {doc.reference_number} — {doc.title}
ላካ: {from_user.get_full_name() or from_user.username}
ማስታወሻ: {note or '—'}

ለማየት: https://muleedms.pythonanywhere.com/documents/{doc.pk}/

ወልድያ ከተማ አስተዳደር — EDMS
        """
        send_mail(
            subject, message,
            settings.DEFAULT_FROM_EMAIL,
            [to_user.email],
            fail_silently=True,
        )
    except Exception:
        pass


# ──────────────────────────── INBOX (Forwarded to me) ────────────────

@login_required
def inbox(request):
    from .models import DocumentForward
    forwards = DocumentForward.objects.filter(
        to_user=request.user
    ).select_related('document', 'from_user').order_by('-forwarded_at')

    unread = forwards.filter(is_read=False).count()

    if request.GET.get('mark_read'):
        forwards.filter(is_read=False).update(is_read=True)
        return redirect('inbox')

    return render(request, 'documents/inbox.html', {
        'forwards': forwards,
        'unread':   unread,
    })


@login_required
@require_POST
def mark_forward_read(request, pk):
    from .models import DocumentForward
    fwd = get_object_or_404(DocumentForward, pk=pk, to_user=request.user)
    fwd.is_read = True
    fwd.save(update_fields=['is_read'])
    return redirect('document_detail', pk=fwd.document.pk)


# ──────────────────────────── OFFICIAL LETTER PDF ────────────────────

@login_required
def official_letter_pdf(request, pk):
    """Generate full official Woldiya City Administration letter PDF."""
    doc = get_object_or_404(Document, pk=pk)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, HRFlowable, Image,
                                        KeepTogether)
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from io import BytesIO
        from documents.utils import to_ethiopian

        # ── Register Ethiopic font ──────────────────────────────────
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'ethiopic.ttf')
        AM  = 'Helvetica'
        AMB = 'Helvetica-Bold'
        if os.path.exists(font_path):
            try:
                if 'Ethiopic' not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont('Ethiopic', font_path))
                AM = AMB = 'Ethiopic'
            except Exception:
                pass

        # ── Colours ────────────────────────────────────────────────
        BRAND  = colors.HexColor('#1B4F72')
        GOLD   = colors.HexColor('#C8960C')
        LIGHT  = colors.HexColor('#F0F4F8')
        BORDER = colors.HexColor('#CBD5E1')
        WHITE  = colors.white
        RED    = colors.HexColor('#C62828')

        # ── Paragraph styles ───────────────────────────────────────
        def sty(name, size=11, bold=False, color=colors.black, align=0, leading=None, space_after=6):
            return ParagraphStyle(
                name, fontName=AMB if bold else AM,
                fontSize=size, textColor=color,
                alignment=align, leading=leading or size * 1.4,
                spaceAfter=space_after,
            )

        # ── Page setup ─────────────────────────────────────────────
        buf  = BytesIO()
        W, H = A4
        page = SimpleDocTemplate(
            buf, pagesize=A4,
            rightMargin=2.2*cm, leftMargin=2.2*cm,
            topMargin=1.8*cm, bottomMargin=2*cm,
            title=f'{doc.reference_number} - {doc.title}',
        )
        story = []
        PW = W - 4.4*cm  # usable width

        # ══════════════════════════════════════════════════════════
        # HEADER — logo + org name + ref/date block
        # ══════════════════════════════════════════════════════════
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'woldiya_logo.png')
        et_date   = to_ethiopian(doc.created_at)
        et_str    = et_date['full'] if et_date else ''
        gc_str    = doc.created_at.strftime('%d/%m/%Y')

        ref_block = Paragraph(
            f'<b>ቁጥር:</b> {doc.reference_number}<br/>'
            f'<b>ቀን:</b> {gc_str}<br/>'
            f'<b>ኢትዮ. ቀን:</b> {et_str}<br/>'
            f'<b>ዓይነት:</b> {doc.get_doc_type_display()}',
            sty('ref', size=9.5, color=BRAND)
        )

        org_block = Paragraph(
            f'<b>ወልድያ ከተማ አስተዳደር</b><br/>'
            f'<font size="9">WOLDIYA CITY ADMINISTRATION</font><br/>'
            f'<font size="8" color="#546E7A">ፈጠራ እና ቴክኖሎጂ — EDMS</font>',
            sty('org', size=15, bold=True, color=BRAND, align=1)
        )

        if os.path.exists(logo_path):
            try:
                logo_img  = Image(logo_path, width=2.8*cm, height=2.8*cm)
                hdr_data  = [[logo_img, org_block, ref_block]]
                hdr_widths = [3.0*cm, PW - 3.0*cm - 5.5*cm, 5.5*cm]
            except Exception:
                hdr_data  = [[org_block, ref_block]]
                hdr_widths = [PW - 5.5*cm, 5.5*cm]
        else:
            hdr_data  = [[org_block, ref_block]]
            hdr_widths = [PW - 5.5*cm, 5.5*cm]

        hdr = Table(hdr_data, colWidths=hdr_widths)
        hdr.setStyle(TableStyle([
            ('VALIGN',   (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN',    (-1,0), (-1,-1), 'RIGHT'),
            ('LEFTPADDING',  (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(hdr)
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width='100%', color=GOLD, thickness=3, spaceAfter=0))
        story.append(HRFlowable(width='100%', color=BRAND, thickness=1, spaceBefore=2, spaceAfter=10))

        # ══════════════════════════════════════════════════════════
        # DOCUMENT TYPE BANNER
        # ══════════════════════════════════════════════════════════
        banner_color = {
            'INCOMING': BRAND,
            'OUTGOING': colors.HexColor('#6A1B9A'),
            'INTERNAL': colors.HexColor('#00695C'),
        }.get(doc.doc_type, BRAND)

        banner = Table(
            [[Paragraph(doc.get_doc_type_display(),
                        sty('ban', size=13, bold=True, color=WHITE, align=1, space_after=0))]],
            colWidths=[PW]
        )
        banner.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,-1), banner_color),
            ('TOPPADDING',   (0,0), (-1,-1), 8),
            ('BOTTOMPADDING',(0,0), (-1,-1), 8),
            ('LEFTPADDING',  (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(banner)
        story.append(Spacer(1, 14))

        # ══════════════════════════════════════════════════════════
        # TO / FROM / SUBJECT block
        # ══════════════════════════════════════════════════════════
        to_from = [
            [Paragraph('ለ  :', sty('lbl', bold=True, color=BRAND)),
             Paragraph(doc.receiver or '—', sty('val', size=11))],
            [Paragraph('ከ  :', sty('lbl', bold=True, color=BRAND)),
             Paragraph(doc.sender or '—',   sty('val', size=11))],
            [Paragraph('ጉዳዩ:', sty('lbl', bold=True, color=BRAND)),
             Paragraph(f'<b>{doc.title}</b>', sty('val', size=11, bold=True))],
        ]
        if doc.due_date:
            et_due = to_ethiopian(doc.due_date)
            due_str = f"{doc.due_date}  ({et_due['full'] if et_due else ''})"
            to_from.append([
                Paragraph('የቀን ገደብ:', sty('lbl', bold=True, color=RED)),
                Paragraph(f'<font color="#C62828"><b>{due_str}</b></font>', sty('val', size=10)),
            ])
        if doc.assigned_to:
            to_from.append([
                Paragraph('ተሰጥቷል:', sty('lbl', bold=True, color=BRAND)),
                Paragraph(doc.assigned_to.get_full_name() or doc.assigned_to.username, sty('val', size=10)),
            ])

        tf_table = Table(to_from, colWidths=[3.2*cm, PW - 3.2*cm])
        tf_table.setStyle(TableStyle([
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING',   (0,0), (-1,-1), 4),
            ('LINEBELOW', (0,0), (-1,-2), 0.5, BORDER),
            ('VALIGN',    (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(tf_table)
        story.append(Spacer(1, 12))
        story.append(HRFlowable(width='100%', color=BORDER, thickness=0.8, spaceAfter=12))

        # ══════════════════════════════════════════════════════════
        # BODY / DESCRIPTION
        # ══════════════════════════════════════════════════════════
        story.append(Paragraph('ዝርዝር ይዘት / ማብራሪያ:', sty('h2', size=11, bold=True, color=BRAND, space_after=8)))

        body_text = doc.description.strip() if doc.description else '— (ምንም ዝርዝር አልተጻፈም) —'
        story.append(Paragraph(
            body_text.replace('\n', '<br/>'),
            sty('body', size=11, leading=20, space_after=16)
        ))
        story.append(Spacer(1, 8))

        # ══════════════════════════════════════════════════════════
        # STATUS / PRIORITY / CATEGORY summary bar
        # ══════════════════════════════════════════════════════════
        status_color = {
            'DRAFT':        colors.HexColor('#546E7A'),
            'PENDING':      colors.HexColor('#E65100'),
            'IN_PROGRESS':  colors.HexColor('#1976D2'),
            'UNDER_REVIEW': colors.HexColor('#6A1B9A'),
            'APPROVED':     colors.HexColor('#2E7D32'),
            'COMPLETED':    colors.HexColor('#1B5E20'),
            'ARCHIVED':     colors.HexColor('#455A64'),
        }.get(doc.status, BRAND)

        priority_color = {
            'LOW': colors.HexColor('#388E3C'),
            'MEDIUM': colors.HexColor('#0277BD'),
            'HIGH': colors.HexColor('#EF6C00'),
            'URGENT': RED,
        }.get(doc.priority, BRAND)

        summary = Table([[
            Paragraph(f'ሁኔታ: {doc.get_status_display()}',   sty('s1', size=9.5, bold=True, color=WHITE, align=1, space_after=0)),
            Paragraph(f'ቅድሚያ: {doc.get_priority_display()}', sty('s2', size=9.5, bold=True, color=WHITE, align=1, space_after=0)),
            Paragraph(f'ምድብ: {doc.category or "—"}',         sty('s3', size=9.5, color=BRAND, align=1, space_after=0)),
        ]], colWidths=[PW/3, PW/3, PW/3])
        summary.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (0,0), status_color),
            ('BACKGROUND',   (1,0), (1,0), priority_color),
            ('BACKGROUND',   (2,0), (2,0), LIGHT),
            ('TOPPADDING',   (0,0), (-1,-1), 7),
            ('BOTTOMPADDING',(0,0), (-1,-1), 7),
            ('BOX',          (0,0), (-1,-1), 0.5, BORDER),
            ('INNERGRID',    (0,0), (-1,-1), 0.5, BORDER),
            ('ROUNDEDCORNERS', [4]),
        ]))
        story.append(summary)

        # ══════════════════════════════════════════════════════════
        # ══════════════════════════════════════════════════════════
        # SIGNATURE AREA (pushed to bottom)
        # ══════════════════════════════════════════════════════════
        story.append(Spacer(1, 60))

        creator_name = doc.created_by.get_full_name() or doc.created_by.username if doc.created_by else ''
        sig = Table([[
            Paragraph(f'<b>የሰነዱ አዘጋጅ ፊርማ</b><br/><font size="8">{creator_name}</font>',
                       sty('sig1', size=10, align=1, leading=16, space_after=0)),
            Paragraph(f'<b>ኃላፊ / አፅዳቂ ፊርማ</b>',
                       sty('sig2', size=10, align=1, leading=16, space_after=0)),
            Paragraph(f'<b>ቀን / Date</b><br/><font size="8">{gc_str}</font>',
                       sty('sig3', size=10, align=1, leading=16, space_after=0)),
        ]], colWidths=[PW/3, PW/3, PW/3])
        sig.setStyle(TableStyle([
            ('TOPPADDING',    (0,0), (-1,-1), 30),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
            ('LINEABOVE',     (0,0), (0,0), 1.2, colors.HexColor('#374151')),
            ('LINEABOVE',     (1,0), (1,0), 1.2, colors.HexColor('#374151')),
            ('LINEABOVE',     (2,0), (2,0), 1.2, colors.HexColor('#374151')),
            ('LEFTPADDING',   (0,0), (-1,-1), 12),
            ('RIGHTPADDING',  (0,0), (-1,-1), 12),
        ]))
        story.append(KeepTogether([sig]))

        # ══════════════════════════════════════════════════════════
        # FOOTER
        # ══════════════════════════════════════════════════════════
        story.append(Spacer(1, 24))
        story.append(HRFlowable(width='100%', color=GOLD, thickness=3, spaceAfter=2))
        story.append(HRFlowable(width='100%', color=BRAND, thickness=1.5, spaceAfter=6))

        footer_table = Table([[
            Paragraph(
                f'<b>ወልድያ ከተማ አስተዳደር</b><br/>'
                f'<font size="7">WOLDIYA CITY ADMINISTRATION</font>',
                sty('ft1', size=8, color=BRAND, align=0, leading=11, space_after=0)
            ),
            Paragraph(
                f'<font size="7">ፈጠራ እና ቴክኖሎጂ ቡድን | EDMS</font><br/>'
                f'<font size="7">muleedms.pythonanywhere.com</font>',
                sty('ft2', size=8, color=BRAND, align=1, leading=11, space_after=0)
            ),
            Paragraph(
                f'<b>ቁጥር:</b> {doc.reference_number}<br/>'
                f'<font size="7">ህትመት: {gc_str}</font>',
                sty('ft3', size=8, color=BRAND, align=2, leading=11, space_after=0)
            ),
        ]], colWidths=[PW/3, PW/3, PW/3])
        footer_table.setStyle(TableStyle([
            ('TOPPADDING',   (0,0), (-1,-1), 4),
            ('BOTTOMPADDING',(0,0), (-1,-1), 4),
            ('LEFTPADDING',  (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('VALIGN',       (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(footer_table)
        story.append(HRFlowable(width='100%', color=GOLD, thickness=1.5, spaceBefore=4))

        # ── Build and return ───────────────────────────────────────
        page.build(story)
        buf.seek(0)
        safe_ref = doc.reference_number.replace('/', '_').replace('.', '_')
        response = HttpResponse(buf.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="letter_{safe_ref}.pdf"'
        return response

    except ImportError:
        messages.error(request, 'reportlab not installed.')
        return redirect('document_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'PDF error: {e}')
        return redirect('document_detail', pk=pk)


# ──────────────────────────── PASSWORD CHANGE ────────────────────────

@login_required
def change_password(request):
    if request.method == 'POST':
        current  = request.POST.get('current_password', '').strip()
        new_pw   = request.POST.get('new_password', '').strip()
        confirm  = request.POST.get('confirm_password', '').strip()

        if not request.user.check_password(current):
            messages.error(request, 'የአሁኑ ፓስዎርድ ትክክል አይደለም።')
        elif len(new_pw) < 8:
            messages.error(request, 'አዲሱ ፓስዎርድ ቢያንስ 8 ፊደላት ይኑሩት።')
        elif new_pw != confirm:
            messages.error(request, 'ፓስዎርዶች አይዛመዱም።')
        else:
            request.user.set_password(new_pw)
            request.user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, request.user)
            messages.success(request, 'ፓስዎርድ ተቀይሯል!')
            return redirect('profile')

    return render(request, 'documents/change_password.html')


# ──────────────────────────── QR SCANNER ─────────────────────────────

@login_required
def qr_scanner(request):
    """QR code scanner page — scans QR and redirects to document."""
    if request.method == 'POST':
        scanned = request.POST.get('scanned_url', '').strip()
        if not scanned:
            messages.error(request, 'QR Code አልተነበበም። እንደገና ይሞክሩ።')
            return redirect('qr_scanner')

        # Extract document ID from URL like /documents/5/ or full URL
        import re
        match = re.search(r'/documents/(\d+)/', scanned)
        if match:
            doc_id = match.group(1)
            return redirect('document_detail', pk=doc_id)

        # Try reference number search
        doc = Document.objects.filter(reference_number__iexact=scanned).first()
        if doc:
            return redirect('document_detail', pk=doc.pk)

        messages.warning(request, f'ደብዳቤ አልተገኘም። የተነበበው: {scanned[:100]}')
        return redirect('qr_scanner')

    return render(request, 'documents/qr_scanner.html')


# ──────────────────────────── ADMIN RESET PASSWORD ───────────────────

@login_required
def reset_user_password(request, user_id):
    """Admin resets any user's password."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')

    target = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        new_pw  = request.POST.get('new_password', '').strip()
        confirm = request.POST.get('confirm_password', '').strip()

        if len(new_pw) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        elif new_pw != confirm:
            messages.error(request, 'Passwords do not match.')
        else:
            target.set_password(new_pw)
            target.save()
            # Send email notification
            if target.email:
                try:
                    from django.core.mail import send_mail
                    send_mail(
                        'Your EDMS Password Has Been Reset',
                        f'Dear {target.get_full_name() or target.username},\n\n'
                        f'Your password has been reset by the administrator.\n\n'
                        f'New password: {new_pw}\n\n'
                        f'Please login and change your password immediately.\n\n'
                        f'Website: https://muleedms.pythonanywhere.com\n\n'
                        f'Woldiya City Administration EDMS',
                        settings.DEFAULT_FROM_EMAIL,
                        [target.email],
                        fail_silently=True,
                    )
                except Exception:
                    pass
            messages.success(request, f'Password for "{target.username}" reset successfully!')
            return redirect('user_management')

    return render(request, 'documents/reset_password.html', {'target': target})


# ──────────────────────────── ATTACHMENTS ────────────────────────────

@login_required
@registrar_required
@require_POST
def upload_attachment(request, pk):
    """Upload additional files to a document."""
    from .models import DocumentAttachment
    doc  = get_object_or_404(Document, pk=pk)
    file = request.FILES.get('file')
    desc = request.POST.get('description', '').strip()

    if not file:
        messages.error(request, 'No file selected.')
        return redirect('document_detail', pk=pk)

    # Validate extension
    ext     = file.name.rsplit('.', 1)[-1].lower()
    allowed = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'tiff', 'bmp', 'doc', 'docx']
    if ext not in allowed:
        messages.error(request, f'File type .{ext} not allowed.')
        return redirect('document_detail', pk=pk)

    if file.size > 20 * 1024 * 1024:
        messages.error(request, 'File exceeds 20MB limit.')
        return redirect('document_detail', pk=pk)

    DocumentAttachment.objects.create(
        document=doc,
        file=file,
        description=desc,
        uploaded_by=request.user,
    )
    log_activity(doc, request.user, 'Attachment uploaded', f'"{file.name}" added.')
    messages.success(request, f'File "{file.name}" uploaded successfully!')
    return redirect('document_detail', pk=pk)


@login_required
@admin_required
def delete_attachment(request, pk, att_id):
    """Delete an attachment from a document."""
    from .models import DocumentAttachment
    att = get_object_or_404(DocumentAttachment, pk=att_id, document_id=pk)
    if request.method == 'POST':
        name = att.filename
        att.file.delete(save=False)
        att.delete()
        messages.warning(request, f'Attachment "{name}" deleted.')
    return redirect('document_detail', pk=pk)
