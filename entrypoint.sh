#!/bin/sh

# Pull the latest changes from the Git repository
git pull origin main

# Apply database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start the Django server
exec "$@"
