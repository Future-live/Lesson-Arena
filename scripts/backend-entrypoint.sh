#!/bin/sh
set -e

cd /app/backend

if [ -f "/app/backend/.env.cloudbase" ]; then
  set -a
  # shellcheck disable=SC1091
  . /app/backend/.env.cloudbase
  set +a
fi

python -c "
import os, time
create_database = os.getenv('MYSQL_CREATE_DATABASE', 'False').lower() in {'1', 'true', 'yes', 'on'}
if create_database and os.getenv('DB_ENGINE', 'sqlite').lower() in {'mysql', 'mariadb'} and not os.getenv('DATABASE_URL'):
    import pymysql
    host = os.getenv('MYSQL_HOST', '127.0.0.1')
    port = int(os.getenv('MYSQL_PORT', '3306'))
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '')
    database = os.getenv('MYSQL_DATABASE', os.getenv('MYSQL_DB', 'lesson_review'))
    quote = chr(96)
    database = database.replace(quote, '')
    for index in range(30):
        try:
            connection = pymysql.connect(host=host, port=port, user=user, password=password, connect_timeout=3)
            with connection.cursor() as cursor:
                cursor.execute(
                    f'CREATE DATABASE IF NOT EXISTS {quote}{database}{quote} '
                    'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
                )
            connection.commit()
            connection.close()
            print('MySQL database is ready')
            break
        except Exception as exc:
            print(f'Waiting for MySQL ({index + 1}/30): {exc}')
            time.sleep(2)
    else:
        raise SystemExit('MySQL database initialization failed')
"

python -c "
import os, time
if os.getenv('DB_ENGINE', 'sqlite').lower() in {'postgres', 'postgresql', 'mysql', 'mariadb'} or os.getenv('DATABASE_URL'):
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
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout "${GUNICORN_TIMEOUT:-120}"
