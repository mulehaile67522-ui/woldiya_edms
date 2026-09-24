FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start: migrate, create admin, collect static, then serve
CMD sh -c "python manage.py migrate --run-syncdb && python manage.py create_admin && python manage.py collectstatic --noinput && gunicorn edms_project.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"
