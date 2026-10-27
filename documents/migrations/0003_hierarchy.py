from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_documentforward'),
    ]

    operations = [
        # Add new fields to UserProfile
        migrations.AddField(
            model_name='userprofile',
            name='org_level',
            field=models.CharField(
                choices=[('CITY','ከተማ አስተዳደር'),('DEPT','መምሪያ / ቢሮ'),('SUBCITY','ክፍለ ከተማ')],
                default='DEPT', max_length=10, verbose_name='የድርጅት ደረጃ'
            ),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='subcity',
            field=models.CharField(
                blank=True, max_length=20, verbose_name='ክፍለ ከተማ',
                choices=[('','— ምረጥ —'),('TALAKU_RASALI','ታላቁ ራሳሊ ክፍለ ከተማ'),('YEJU','የጁ ክፍለ ከተማ'),('TAYITU','ጣይቱ ክፍለ ከተማ')],
            ),
        ),
        # Alter role field to include new roles
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.CharField(
                choices=[
                    ('MAYOR',      'ከንቲባ'),
                    ('VICE_MAYOR', 'ምክትል ከንቲባ'),
                    ('ADMIN',      'አስተዳዳሪ (IT)'),
                    ('DEPT_HEAD',  'የቢሮ/መምሪያ ኃላፊ'),
                    ('REGISTRAR',  'ሰናዳ'),
                    ('SUBCITY',    'ክፍለ ከተማ'),
                    ('VIEWER',     'ተመልካች'),
                ],
                default='VIEWER', max_length=15, verbose_name='ሚና'
            ),
        ),
        # Alter department field to allow longer names
        migrations.AlterField(
            model_name='userprofile',
            name='department',
            field=models.CharField(blank=True, max_length=150, verbose_name='ቢሮ / መምሪያ'),
        ),
        # Create Department model
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True, verbose_name='የቢሮ/መምሪያ ስም')),
                ('short_name', models.CharField(blank=True, max_length=50, verbose_name='አጭር ስም')),
                ('level', models.CharField(
                    choices=[('CITY','ከተማ አስተዳደር'),('DEPT','መምሪያ / ቢሮ'),('SUBCITY','ክፍለ ከተማ')],
                    default='DEPT', max_length=10, verbose_name='ደረጃ'
                )),
                ('parent', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='children', to='documents.department',
                    verbose_name='ሪፖርት ለሚያደርጉለት'
                )),
                ('is_active', models.BooleanField(default=True, verbose_name='ንቁ')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='ቅደም ተከተል')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'ቢሮ / መምሪያ',
                'verbose_name_plural': 'ቢሮዎች / መምሪያዎች',
                'ordering': ['order', 'name'],
            },
        ),
    ]
