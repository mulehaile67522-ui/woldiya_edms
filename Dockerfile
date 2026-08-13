FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD python manage.py migrate --run-syncdb && \
    python manage.py collectstatic --noinput --ignore=*.scss || true && \
    gunicorn edms_project.wsgi --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level debug
