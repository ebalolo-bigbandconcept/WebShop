#!/bin/bash
set -e

echo "Starting backend initialization..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! nc -z db 5432; do
  sleep 0.5
done
echo "PostgreSQL is ready!"

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Initialize default data (admin user, TVA rates, etc.)
echo "Initializing default data..."
python init_db.py

# Start the application
echo "Starting Flask application..."
exec python app.py
