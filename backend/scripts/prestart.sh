#! /usr/bin/env bash

set -e
set -x

# Run migrations
python manage.py migrate --noinput

# Create initial data in DB
python manage.py create_initial_data

# Collect Django admin static files: uploaded to object storage when
# AWS_STORAGE_BUCKET_NAME is set, otherwise copied to STATIC_ROOT
python manage.py collectstatic --noinput
