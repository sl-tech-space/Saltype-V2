#!/bin/bash

# マイグレーション実行
gosu django python manage.py makemigrations
gosu django python manage.py migrate

# Gunicornを非rootユーザー(django)で実行
exec gosu django gunicorn config.wsgi:application --bind 0.0.0.0:8000
