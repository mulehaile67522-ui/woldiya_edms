web: python manage.py migrate --run-syncdb && python manage.py collectstatic --noinput && gunicorn edms_project.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 120
