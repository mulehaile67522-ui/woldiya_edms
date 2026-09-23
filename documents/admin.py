from django.contrib import admin
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import (Document, Category, Notification,
                     ActivityLog, UserProfile,
                     InnovationProject, Training)


# ── Inline UserProfile inside User admin ──────────────────────────────
class UserProfileInline(admin.StackedInline):
    model       = UserProfile
    can_delete  = False
    verbose_name_plural = 'መረጃ'
    fields      = ('role', 'department', 'phone')


class UserAdmin(BaseUserAdmin):
    inlines     = (UserProfileInline,)
    list_display = ('username', 'get_full_name', 'email', 'get_role', 'get_dept', 'is_active')

    def get_role(self, obj):
        try: return obj.profile.get_role_display()
        except: return '—'
    get_role.short_description = 'ሚና'

    def get_dept(self, obj):
        try: return obj.profile.department or '—'
        except: return '—'
    get_dept.short_description = 'ክፍል'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ── Document ──────────────────────────────────────────────────────────
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display  = ('reference_number', 'title', 'doc_type_badge',
                     'status_badge', 'priority_badge', 'sender',
                     'receiver', 'due_date', 'created_at')
    list_filter   = ('doc_type', 'status', 'priority', 'category', 'created_at')
    search_fields = ('reference_number', 'title', 'sender', 'receiver', 'description')
    readonly_fields = ('created_at', 'updated_at', 'view_count', 'download_count')
    ordering      = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25

    fieldsets = (
        ('መሠረታዊ መረጃ', {
            'fields': ('title', 'reference_number', 'doc_type', 'category')
        }),
        ('ላኪ እና ተቀባይ', {
            'fields': ('sender', 'receiver', 'assigned_to')
        }),
        ('ሁኔታ', {
            'fields': ('status', 'priority', 'date_received', 'due_date')
        }),
        ('ፋይል', {
            'fields': ('file', 'description')
        }),
        ('ስታቲስቲክስ', {
            'fields': ('view_count', 'download_count', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def doc_type_badge(self, obj):
        colors = {'INCOMING': '#1565c0', 'OUTGOING': '#6a1b9a', 'INTERNAL': '#00695c'}
        c = colors.get(obj.doc_type, '#546e7a')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:.8rem;">{}</span>',
            c, obj.get_doc_type_display()
        )
    doc_type_badge.short_description = 'ዓይነት'

    def status_badge(self, obj):
        colors = {'PENDING': '#e65100', 'IN_PROGRESS': '#1976d2',
                  'COMPLETED': '#2e7d32', 'ARCHIVED': '#546e7a'}
        c = colors.get(obj.status, '#546e7a')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:.8rem;">{}</span>',
            c, obj.get_status_display()
        )
    status_badge.short_description = 'ሁኔታ'

    def priority_badge(self, obj):
        colors = {'URGENT': '#c62828', 'HIGH': '#ef6c00',
                  'MEDIUM': '#0277bd', 'LOW': '#388e3c'}
        c = colors.get(obj.priority, '#546e7a')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:.8rem;">{}</span>',
            c, obj.get_priority_display()
        )
    priority_badge.short_description = 'ቅድሚያ'


# ── Category ──────────────────────────────────────────────────────────
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('amharic_name', 'name', 'doc_count', 'description_short', 'created_at')
    search_fields = ('name', 'amharic_name', 'description')
    ordering      = ('name',)

    def doc_count(self, obj):
        return obj.documents.count()
    doc_count.short_description = 'ደብዳቤዎች'

    def description_short(self, obj):
        return obj.description[:60] + '...' if len(obj.description) > 60 else obj.description
    description_short.short_description = 'መግለጫ'


# ── ActivityLog ───────────────────────────────────────────────────────
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display  = ('timestamp', 'user', 'document', 'action', 'detail_short')
    list_filter   = ('action', 'timestamp')
    search_fields = ('action', 'detail', 'user__username', 'document__reference_number')
    readonly_fields = ('timestamp',)
    ordering      = ('-timestamp',)
    list_per_page = 50

    def detail_short(self, obj):
        return obj.detail[:60] + '...' if len(obj.detail) > 60 else obj.detail
    detail_short.short_description = 'ዝርዝር'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ── Notification ──────────────────────────────────────────────────────
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ('user', 'message_short', 'is_read', 'created_at')
    list_filter   = ('is_read', 'created_at')
    search_fields = ('message', 'user__username')
    ordering      = ('-created_at',)
    actions       = ['mark_read', 'mark_unread']

    def message_short(self, obj):
        return obj.message[:80] + '...' if len(obj.message) > 80 else obj.message
    message_short.short_description = 'መልዕክት'

    def mark_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'{queryset.count()} ማሳወቂያዎች እንደተነበቡ ምልክት ተደርጓል።')
    mark_read.short_description = 'እንደተነበቡ ምልክት አድርግ'

    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f'{queryset.count()} ማሳወቂያዎች ያልተነበቡ ሆኑ።')
    mark_unread.short_description = 'እንዳልተነበቡ ምልክት አድርግ'


# ── InnovationProject ─────────────────────────────────────────────────
@admin.register(InnovationProject)
class InnovationProjectAdmin(admin.ModelAdmin):
    list_display  = ('title', 'status', 'lead', 'start_date', 'end_date', 'created_at')
    list_filter   = ('status',)
    search_fields = ('title', 'description')


# ── Training ──────────────────────────────────────────────────────────
@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    list_display  = ('title', 'trainer', 'date', 'duration', 'participant_count')
    list_filter   = ('date',)
    search_fields = ('title', 'trainer')
    filter_horizontal = ('participants',)

    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'ተሳታፊዎች'


# ── Admin site branding ───────────────────────────────────────────────
admin.site.site_header  = 'ወልድያ ከተማ አስተዳደር — EDMS'
admin.site.site_title   = 'EDMS Admin'
admin.site.index_title  = 'የስርዓት አስተዳደር'
