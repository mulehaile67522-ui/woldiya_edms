"""
Management command: create_admin
Creates the initial superuser from environment variables.
Safe to run multiple times — skips if the user already exists.

Usage (Railway start command or manual):
  python manage.py create_admin

Required env vars:
  DJANGO_SUPERUSER_USERNAME   (default: admin)
  DJANGO_SUPERUSER_PASSWORD   (default: Admin@1234)
  DJANGO_SUPERUSER_EMAIL      (default: admin@woldiya.gov.et)
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create initial superuser from environment variables (idempotent)'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@1234')
        email    = os.environ.get('DJANGO_SUPERUSER_EMAIL',    'admin@woldiya.gov.et')
        update_password = os.environ.get('DJANGO_SUPERUSER_UPDATE_PASSWORD', '').lower() in ('1', 'true', 'yes')

        user = User.objects.filter(username=username).first()
        if user:
          if update_password:
            user.set_password(password)
            user.email = email
            user.save(update_fields=['password', 'email'])
            self.stdout.write(self.style.SUCCESS(
              f'Superuser "{username}" password updated successfully.'
            ))
            return
            self.stdout.write(self.style.WARNING(
                f'Superuser "{username}" already exists — skipping.'
            ))
            return

        User.objects.create_superuser(username=username, password=password, email=email)
        self.stdout.write(self.style.SUCCESS(
            f'Superuser "{username}" created successfully.'
        ))
