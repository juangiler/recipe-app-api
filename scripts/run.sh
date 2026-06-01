#!/usr/bin/env sh
set -e

# log out the permissions of the /vol directory for debugging
ls -ld /vol


# Wait for the DB to be ready, then migrate
python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py migrate

exec gunicorn -c /app/gunicorn_conf.py core.asgi:application