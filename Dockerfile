FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=mindvibe_project.settings

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY outfits /app/outfits
COPY manage.py /app/
COPY mindvibe_project /app/mindvibe_project

RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "mindvibe_project.wsgi:application", "--bind", "0.0.0.0:8000"]
