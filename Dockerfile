FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p staticfiles static/img media

EXPOSE 8000

CMD sh -c "python manage.py migrate --run-syncdb && gunicorn edms_project.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --log-level debug 2>&1"
