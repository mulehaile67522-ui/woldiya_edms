from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create a ZIP backup of the database and uploaded documents'

    def handle(self, *args, **options):
        backup_dir = settings.BASE_DIR / 'backups'
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_path = backup_dir / f'edms_backup_{timestamp}.zip'

        with ZipFile(archive_path, 'w', ZIP_DEFLATED) as archive:
            database_path = Path(settings.DATABASES['default']['NAME'])
            if database_path.exists():
                archive.write(database_path, database_path.relative_to(settings.BASE_DIR))

            media_root = Path(settings.MEDIA_ROOT)
            if media_root.exists():
                for file_path in media_root.rglob('*'):
                    if file_path.is_file():
                        archive.write(file_path, file_path.relative_to(settings.BASE_DIR))

        self.stdout.write(self.style.SUCCESS(f'Backup created: {archive_path}'))