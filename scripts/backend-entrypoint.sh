#!/bin/sh
set -e

cd /app/backend

python -c "
import os, time
if os.getenv('DB_ENGINE', 'sqlite').lower() == 'postgres':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    from django.db import connection
    for index in range(30):
        try:
            connection.ensure_connection()
            print('Database is ready')
            break
        except Exception as exc:
            print(f'Waiting for database ({index + 1}/30): {exc}')
            time.sleep(2)
    else:
        raise SystemExit('Database connection failed')
"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.getenv('DJANGO_SUPERUSER_USERNAME')
email = os.getenv('DJANGO_SUPERUSER_EMAIL')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD')
if username and email and password:
    user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
    user.email = email
    user.display_name = '系统管理员'
    user.role = 'admin'
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    print('Superuser ensured')
"

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}"
