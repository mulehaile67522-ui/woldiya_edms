#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --run-syncdb
python manage.py create_admin
python seed_categories.py || true
python manage.py seed_demo_data || true
