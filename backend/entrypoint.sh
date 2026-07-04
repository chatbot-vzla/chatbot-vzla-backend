#!/bin/sh

# Asegurar que el script falle ante cualquier error
set -e

echo "Ejecutando makemigrations..."
python manage.py makemigrations --noinput

echo "Ejecutando migrate..."
python manage.py migrate --noinput

echo "Iniciando la aplicación..."
exec "$@"
