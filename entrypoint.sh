#!/bin/sh
set -e

python manage.py migrate --noinput

case "$DEBUG" in
  True|true|1) ;;
  *) python manage.py collectstatic --noinput ;;
esac

exec "$@"