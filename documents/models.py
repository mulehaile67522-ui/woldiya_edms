from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import os


# ──────────────────────────────────────────────
#  USER PROFILE  (roles)
# ──────────────────────────────────────────────

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN',      'አስተዳዳሪ'),
        ('REGISTRAR',  'ሰናዳ'),
        ('VIEWER',     'ተመልካች'),
    ]
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role       = models.CharField(max_length=12, choices=ROLE_CHOICES, default='VIEWER')
    department = models.CharField(max_length=100, blank=True, verbose_name='ክፍል / ቢሮ')
    phone      = models.CharField(max_length=20, blank=True, verbose_name='ስልክ ቁጥር')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'የተጠቃሚ መረጃ'
        verbose_name_plural = 'የተጠቃሚዎች መረጃ'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def is_admin(self):      return self.role == 'ADMIN'
    def is_registrar(self):  return self.role in ('ADMIN', 'REGISTRAR')
    def can_edit(self):      return self.role in ('ADMIN', 'REGISTRAR')


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.get_or_create(user=instance)


# ──────────────────────────────────────────────
#  ACTIVITY LOG
# ──────────────────────────────────────────────

class ActivityLog(models.Model):
    document  = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='activities')
    user      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action    = models.CharField(max_length=100, verbose_name='እርምጃ')
    detail    = models.TextField(blank=True, verbose_name='ዝርዝር')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='ጊዜ')

    class Meta:
        ordering            = ['-timestamp']
        verbose_name        = 'የእንቅስቃሴ ታሪክ'
        verbose_name_plural = 'የእንቅስቃሴ ታሪኮች'

    def __str__(self):
        return f"{self.action} — {self.document}"


# ──────────────────────────────────────────────
#  NOTIFICATION
# ──────────────────────────────────────────────

class Notification(models.Model):
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message   = models.TextField(verbose_name='መልዕክት')
    link      = models.CharField(max_length=200, blank=True)
    is_read   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'ማሳወቂያ'
        verbose_name_plural = 'ማሳወቂያዎች'

    def __str__(self):
        return f"ማሳወቂያ — {self.user.username}"


# ──────────────────────────────────────────────
#  CATEGORY
# ──────────────────────────────────────────────

class Category(models.Model):
    name         = models.CharField(max_length=100, unique=True, verbose_name='ምድብ')
    amharic_name = models.CharField(max_length=100, blank=True, verbose_name='የአማርኛ ስም')
    description  = models.TextField(blank=True, verbose_name='መግለጫ')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'ምድብ'
        verbose_name_plural = 'ምድቦች'
        ordering            = ['name']

    def __str__(self):
        return self.amharic_name if self.amharic_name else self.name


# ──────────────────────────────────────────────
#  DOCUMENT
# ──────────────────────────────────────────────

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('INCOMING', 'ገቢ ደብዳቤ'),
        ('OUTGOING', 'ወጪ ደብዳቤ'),
        ('INTERNAL', 'የውስጥ ማስታወሻ'),
    ]
    STATUS_CHOICES = [
        ('PENDING',     'በመጠባበቅ ላይ'),
        ('IN_PROGRESS', 'በሂደት ላይ'),
        ('COMPLETED',   'ተጠናቋል'),
        ('ARCHIVED',    'ተቀምጧል'),
    ]
    PRIORITY_CHOICES = [
        ('LOW',    'ዝቅተኛ'),
        ('MEDIUM', 'መካከለኛ'),
        ('HIGH',   'ከፍተኛ'),
        ('URGENT', 'አስቸኳይ'),
    ]

    title            = models.CharField(max_length=255, verbose_name='የደብዳቤው ርዕስ')
    reference_number = models.CharField(max_length=100, unique=True, verbose_name='የደብዳቤ ቁጥር')
    doc_type         = models.CharField(max_length=10, choices=DOCUMENT_TYPES, verbose_name='ዓይነት')
    category         = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='documents', verbose_name='ምድብ')
    sender           = models.CharField(max_length=255, verbose_name='ላኪ')
    receiver         = models.CharField(max_length=255, verbose_name='ተቀባይ')
    description      = models.TextField(blank=True, verbose_name='መግለጫ / ማስታወሻ')
    file             = models.FileField(upload_to='documents/%Y/%m/', blank=True, null=True,
                                         verbose_name='ፋይል (PDF/Image)')
    assigned_to      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='assigned_documents', verbose_name='የተመደበለት')
    status           = models.CharField(max_length=15, choices=STATUS_CHOICES,
                                         default='PENDING', verbose_name='ሁኔታ')
    priority         = models.CharField(max_length=10, choices=PRIORITY_CHOICES,
                                         default='MEDIUM', verbose_name='ቅድሚያ')
    date_received    = models.DateField(null=True, blank=True, verbose_name='የደረሰበት ቀን')
    due_date         = models.DateField(null=True, blank=True, verbose_name='የመጨረሻ ቀን')
    created_at       = models.DateTimeField(auto_now_add=True, verbose_name='የተመዘገበበት ቀን')
    updated_at       = models.DateTimeField(auto_now=True, verbose_name='ዝመና')
    created_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='documents_created', verbose_name='የተመዘገበው')
    download_count   = models.PositiveIntegerField(default=0, verbose_name='የወረዱ ብዛት')
    view_count       = models.PositiveIntegerField(default=0, verbose_name='የታዩ ብዛት')

    class Meta:
        verbose_name        = 'ደብዳቤ'
        verbose_name_plural = 'ደብዳቤዎች'
        ordering            = ['-created_at']

    def __str__(self):
        return f"{self.reference_number} - {self.title}"

    def get_file_extension(self):
        if self.file:
            _, ext = os.path.splitext(self.file.name)
            return ext.lower()
        return ''

    @property
    def is_pdf(self):
        return self.get_file_extension() == '.pdf'

    @property
    def is_image(self):
        return self.get_file_extension() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

    def get_priority_color(self):
        return {'LOW':'success','MEDIUM':'info','HIGH':'warning','URGENT':'danger'}.get(self.priority,'secondary')

    def get_status_color(self):
        return {'PENDING':'warning','IN_PROGRESS':'primary','COMPLETED':'success','ARCHIVED':'secondary'}.get(self.status,'secondary')

    def ethiopian_year(self):
        """Return approximate Ethiopian fiscal year."""
        gc_year = self.created_at.year
        gc_month = self.created_at.month
        # Ethiopian New Year starts ~Sep 11
        et_year = gc_year - 8 if gc_month >= 9 else gc_year - 9
        return et_year

    def days_since_created(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).days


# ──────────────────────────────────────────────
#  CAPACITY BUILDING — Innovation Projects
# ──────────────────────────────────────────────

class InnovationProject(models.Model):
    STATUS = [
        ('PLANNING',    'ዕቅድ ላይ'),
        ('ACTIVE',      'በሂደት'),
        ('COMPLETED',   'ተጠናቋል'),
        ('ON_HOLD',     'ቆሟል'),
    ]
    title        = models.CharField(max_length=200, verbose_name='ርዕስ')
    description  = models.TextField(verbose_name='መግለጫ')
    lead         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='led_projects', verbose_name='ኃላፊ')
    status       = models.CharField(max_length=12, choices=STATUS, default='PLANNING')
    start_date   = models.DateField(null=True, blank=True)
    end_date     = models.DateField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'የፈጠራ ፕሮጀክት'
        verbose_name_plural = 'የፈጠራ ፕሮጀክቶች'

    def __str__(self):
        return self.title


# ──────────────────────────────────────────────
#  CAPACITY BUILDING — Training
# ──────────────────────────────────────────────

class Training(models.Model):
    title        = models.CharField(max_length=200, verbose_name='የሥልጠና ርዕስ')
    description  = models.TextField(blank=True)
    trainer      = models.CharField(max_length=150, blank=True, verbose_name='አሠልጣኝ')
    date         = models.DateField(verbose_name='ቀን')
    duration     = models.PositiveIntegerField(default=1, verbose_name='ቀናት')
    participants = models.ManyToManyField(User, blank=True, related_name='trainings',
                                           verbose_name='ተሳታፊዎች')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-date']
        verbose_name        = 'ሥልጠና'
        verbose_name_plural = 'ሥልጠናዎች'

    def __str__(self):
        return self.title
