#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

# Pull the latest changes from the Git repository
echo "Pulling the latest changes from the repository..."
git pull

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the Django development server
echo "Starting the Django server..."
exec "$@"
