#! /usr/bin/env bash

set -e
set -x

# Run migrations
python manage.py migrate --noinput

# Create initial data in DB
python manage.py create_initial_data
