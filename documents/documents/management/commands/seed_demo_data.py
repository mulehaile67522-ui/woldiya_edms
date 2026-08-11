from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from documents.models import Category, Document, UserProfile
from documents.utils import generate_reference_number


class Command(BaseCommand):
    help = 'Seed demo categories and sample documents for Weldaya EDMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing documents and categories before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Document.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write('Existing documents and categories cleared.')

        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@woldiya.gov.et',
                'first_name': 'System',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Admin user created (admin / admin123)'))
        else:
            self.stdout.write('Admin user already exists.')

        profile, _ = UserProfile.objects.get_or_create(user=admin)
        profile.role = 'ADMIN'
        profile.department = 'ፈጠራ እና ቴክኖሎጂ'
        profile.save()

        categories_data = [
            ('Administration', 'አስተዳደር', 'አስተዳደራዊ ደብዳቤዎች'),
            ('Finance', 'ፋይናንስ', 'የገንዘብ እና በጀት ደብዳቤዎች'),
            ('HR', 'ሰው ሀብት', 'የሰራተኞች እና ሥልጠና'),
            ('Legal', 'ህጋዊ', 'የህግ እና ውሎች'),
            ('Infrastructure', 'መሠረተ ልማት', 'የመሠረተ ልማት ፕሮጀክቶች'),
        ]
        categories = {}
        for name, amharic, desc in categories_data:
            cat, _ = Category.objects.get_or_create(
                name=name,
                defaults={'amharic_name': amharic, 'description': desc},
            )
            categories[name] = cat

        today = timezone.localdate()
        samples = [
            {
                'title': 'የ2019 ዓ.ም የበጀት ዓመት ዕቅድ ማጽደቅ',
                'doc_type': 'INCOMING',
                'category': categories['Finance'],
                'sender': 'አማራ ብሔራዊ ክልል መንግስት',
                'receiver': 'ወልድያ ከተማ አስተዳደር',
                'status': 'IN_PROGRESS',
                'priority': 'HIGH',
                'date_received': today - timedelta(days=5),
                'due_date': today + timedelta(days=10),
            },
            {
                'title': 'የከተማ መሠረተ ልማት ፕሮጀክት ሪፖርት',
                'doc_type': 'OUTGOING',
                'category': categories['Infrastructure'],
                'sender': 'ወልድያ ከተማ አስተዳደር',
                'receiver': 'የከተማ መሠረተ ልማት ቢሮ',
                'status': 'COMPLETED',
                'priority': 'MEDIUM',
                'date_received': today - timedelta(days=20),
                'due_date': today - timedelta(days=2),
            },
            {
                'title': 'የውስጥ ስብሰባ ማስታወሻ — EDMS ስርዓት',
                'doc_type': 'INTERNAL',
                'category': categories['Administration'],
                'sender': 'ፈጠራ እና ቴክኖሎጂ ቡድን',
                'receiver': 'ሁሉም ክፍሎች',
                'status': 'PENDING',
                'priority': 'URGENT',
                'date_received': today - timedelta(days=1),
                'due_date': today + timedelta(days=3),
            },
            {
                'title': 'የሰራተኞች ሥልጠና መርሃ ግብር',
                'doc_type': 'INCOMING',
                'category': categories['HR'],
                'sender': 'የሰው ሀብት ሚኒስቴር',
                'receiver': 'ወልድያ ከተማ HR ቢሮ',
                'status': 'PENDING',
                'priority': 'MEDIUM',
                'date_received': today - timedelta(days=12),
                'due_date': today - timedelta(days=5),
            },
            {
                'title': 'የከተማ ውል ማሻሻያ መመሪያ',
                'doc_type': 'INCOMING',
                'category': categories['Legal'],
                'sender': 'የከተማ ጽ/ቤት',
                'receiver': 'የህግ ጉዳዮች ክፍል',
                'status': 'IN_PROGRESS',
                'priority': 'HIGH',
                'date_received': today - timedelta(days=8),
                'due_date': today + timedelta(days=7),
            },
            {
                'title': 'የዲጂታል ስርዓት መተግበሪያ ጥያቄ',
                'doc_type': 'OUTGOING',
                'category': categories['Administration'],
                'sender': 'ወልድያ ከተማ አስተዳደር',
                'receiver': 'ኢትዮ-ቴሌኮም',
                'status': 'PENDING',
                'priority': 'LOW',
                'date_received': today - timedelta(days=3),
                'due_date': today + timedelta(days=14),
            },
        ]

        created_count = 0
        for sample in samples:
            ref = generate_reference_number(sample['doc_type'])
            while Document.objects.filter(reference_number=ref).exists():
                ref = generate_reference_number(sample['doc_type'])
            _, created = Document.objects.get_or_create(
                title=sample['title'],
                defaults={
                    'reference_number': ref,
                    **sample,
                    'created_by': admin,
                    'assigned_to': admin,
                    'description': f'የማሳያ ደብዳቤ — {sample["title"]}',
                },
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done! {created_count} sample documents, {len(categories)} categories ready.'
        ))
        self.stdout.write('Login: admin / admin123')
