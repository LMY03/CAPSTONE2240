#!/bin/sh

# Pull the latest changes from the repository
echo "Pulling the latest changes from the repository..."
git pull

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the Django server
echo "Starting the Django server..."
exec "$@"
