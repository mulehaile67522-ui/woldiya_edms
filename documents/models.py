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
        ('MAYOR',       'ከንቲባ'),
        ('VICE_MAYOR',  'ምክትል ከንቲባ'),
        ('ADMIN',       'አስተዳዳሪ (IT)'),
        ('DEPT_HEAD',   'የቢሮ/መምሪያ ኃላፊ'),
        ('REGISTRAR',   'ሰናዳ'),
        ('SUBCITY',     'ክፍለ ከተማ'),
        ('VIEWER',      'ተመልካች'),
    ]

    ORG_LEVEL_CHOICES = [
        ('CITY',    'ከተማ አስተዳደር'),
        ('DEPT',    'መምሪያ / ቢሮ'),
        ('SUBCITY', 'ክፍለ ከተማ'),
    ]

    SUBCITY_CHOICES = [
        ('',            '— ምረጥ —'),
        ('TALAKU_RASALI','ታላቁ ራሳሊ ክፍለ ከተማ'),
        ('YEJU',         'የጁ ክፍለ ከተማ'),
        ('TAYITU',       'ጣይቱ ክፍለ ከተማ'),
    ]

    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role       = models.CharField(max_length=15, choices=ROLE_CHOICES, default='VIEWER', verbose_name='ሚና')
    org_level  = models.CharField(max_length=10, choices=ORG_LEVEL_CHOICES, default='DEPT', verbose_name='የድርጅት ደረጃ')
    department = models.CharField(max_length=150, blank=True, verbose_name='ቢሮ / መምሪያ')
    subcity    = models.CharField(max_length=20, choices=SUBCITY_CHOICES, blank=True, verbose_name='ክፍለ ከተማ')
    phone      = models.CharField(max_length=20, blank=True, verbose_name='ስልክ ቁጥር')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'የተጠቃሚ መረጃ'
        verbose_name_plural = 'የተጠቃሚዎች መረጃ'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def is_admin(self):
        return self.role in ('ADMIN', 'MAYOR', 'VICE_MAYOR')

    def is_registrar(self):
        return self.role in ('ADMIN', 'MAYOR', 'VICE_MAYOR', 'DEPT_HEAD', 'REGISTRAR', 'SUBCITY')

    def can_edit(self):
        return self.role in ('ADMIN', 'MAYOR', 'VICE_MAYOR', 'DEPT_HEAD')

    def can_approve(self):
        return self.role in ('MAYOR', 'VICE_MAYOR', 'DEPT_HEAD')

    def sees_all(self):
        """City-level roles see ALL documents."""
        return self.role in ('MAYOR', 'VICE_MAYOR', 'ADMIN')


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
#  DEPARTMENT (ቢሮዎች / መምሪያዎች)
# ──────────────────────────────────────────────

class Department(models.Model):
    LEVEL_CHOICES = [
        ('CITY',    'ከተማ አስተዳደር'),
        ('DEPT',    'መምሪያ / ቢሮ'),
        ('SUBCITY', 'ክፍለ ከተማ'),
    ]

    name       = models.CharField(max_length=150, unique=True, verbose_name='የቢሮ/መምሪያ ስም')
    short_name = models.CharField(max_length=50, blank=True, verbose_name='አጭር ስም')
    level      = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='DEPT', verbose_name='ደረጃ')
    parent     = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='children', verbose_name='ሪፖርት ለሚያደርጉለት')
    is_active  = models.BooleanField(default=True, verbose_name='ንቁ')
    order      = models.PositiveIntegerField(default=0, verbose_name='ቅደም ተከተል')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['order', 'name']
        verbose_name        = 'ቢሮ / መምሪያ'
        verbose_name_plural = 'ቢሮዎች / መምሪያዎች'

    def __str__(self):
        return self.name


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
        ('DRAFT',       'ረቂቅ'),
        ('PENDING',     'በመጠባበቅ ላይ'),
        ('IN_PROGRESS', 'በሂደት ላይ'),
        ('UNDER_REVIEW','በዳኝነት ላይ'),
        ('APPROVED',    'ጸድቋል'),
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
    department       = models.CharField(max_length=100, blank=True, verbose_name='ቢሮ / ክፍል')
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


# ──────────────────────────────────────────────
#  DOCUMENT FORWARDING
# ──────────────────────────────────────────────

class DocumentForward(models.Model):
    """Track when a document is forwarded from one department to another."""
    document     = models.ForeignKey(Document, on_delete=models.CASCADE,
                                      related_name='forwards', verbose_name='ደብዳቤ')
    from_user    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                      related_name='forwarded_docs', verbose_name='ላካ')
    to_user      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                      related_name='received_forwards', verbose_name='ተቀባይ')
    to_department = models.CharField(max_length=100, blank=True, verbose_name='ወደ ቢሮ')
    note         = models.TextField(blank=True, verbose_name='ማስታወሻ')
    is_read      = models.BooleanField(default=False, verbose_name='ታይቷል')
    forwarded_at = models.DateTimeField(auto_now_add=True, verbose_name='የተላከበት ቀን')

    class Meta:
        ordering            = ['-forwarded_at']
        verbose_name        = 'ደብዳቤ ማስተላለፍ'
        verbose_name_plural = 'ደብዳቤ ማስተላለፍዎች'

    def __str__(self):
        return f"{self.document.reference_number} → {self.to_department or self.to_user}"


# ──────────────────────────────────────────────
#  DOCUMENT ATTACHMENT (multiple files per doc)
# ──────────────────────────────────────────────

class DocumentAttachment(models.Model):
    document    = models.ForeignKey(Document, on_delete=models.CASCADE,
                                     related_name='attachments', verbose_name='ደብዳቤ')
    file        = models.FileField(upload_to='attachments/%Y/%m/', verbose_name='ፋይል')
    description = models.CharField(max_length=200, blank=True, verbose_name='መግለጫ')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='የሰቀለው')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='የሰቀለበት ጊዜ')

    class Meta:
        ordering            = ['-uploaded_at']
        verbose_name        = 'ተያያዥ ፋይል'
        verbose_name_plural = 'ተያያዥ ፋይሎች'

    def __str__(self):
        return f"{self.document.reference_number} - {self.file.name}"

    @property
    def filename(self):
        import os
        return os.path.basename(self.file.name)

    @property
    def is_pdf(self):
        return self.filename.lower().endswith('.pdf')

    @property
    def is_image(self):
        return self.filename.lower().rsplit('.', 1)[-1] in ['jpg', 'jpeg', 'png', 'gif', 'bmp']


# ──────────────────────────────────────────────
#  DELETION LOG (survives document deletion)
# ──────────────────────────────────────────────

class DeletionLog(models.Model):
    """Records document deletions — persists even after document is gone."""
    reference_number = models.CharField(max_length=100, verbose_name='የደብዳቤ ቁጥር')
    title            = models.CharField(max_length=255, verbose_name='ርዕስ')
    doc_type         = models.CharField(max_length=10, blank=True)
    department       = models.CharField(max_length=100, blank=True)
    deleted_by       = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                          related_name='deletions', verbose_name='የሰረዘው')
    deleted_at       = models.DateTimeField(auto_now_add=True, verbose_name='የተሰረዘበት ጊዜ')
    reason           = models.TextField(blank=True, verbose_name='ምክንያት')

    class Meta:
        ordering            = ['-deleted_at']
        verbose_name        = 'የስረዛ ታሪክ'
        verbose_name_plural = 'የስረዛ ታሪኮች'

    def __str__(self):
        return f"DELETED: {self.reference_number} by {self.deleted_by}"


# ──────────────────────────────────────────────
#  LOGIN ATTEMPT LOG (security)
# ──────────────────────────────────────────────

class LoginAttempt(models.Model):
    username    = models.CharField(max_length=150, verbose_name='Username')
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    success     = models.BooleanField(default=False, verbose_name='Success')
    timestamp   = models.DateTimeField(auto_now_add=True)
    user_agent  = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering            = ['-timestamp']
        verbose_name        = 'Login Attempt'
        verbose_name_plural = 'Login Attempts'

    def __str__(self):
        status = 'OK' if self.success else 'FAILED'
        return f'{status} — {self.username} @ {self.timestamp}'
