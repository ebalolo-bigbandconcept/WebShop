#!/bin/bash
set -e

echo "Starting backend initialization..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while ! nc -z db 5432; do
  RETRY_COUNT=$((RETRY_COUNT+1))
  if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "ERROR: PostgreSQL did not become ready in time"
    exit 1
  fi
  echo "Waiting for PostgreSQL... ($RETRY_COUNT/$MAX_RETRIES)"
  sleep 1
done
echo "PostgreSQL is ready!"

# Additional wait to ensure PostgreSQL is fully initialized
sleep 2

# Run database migrations
echo "Running database migrations..."
if flask db upgrade; then
  echo "Database migrations completed successfully!"
else
  echo "ERROR: Database migrations failed!"
  exit 1
fi

# Initialize default data (admin user, TVA rates, etc.)
echo "Initializing default data..."
if python init_db.py; then
  echo "Default data initialization completed successfully!"
else
  echo "WARNING: Default data initialization had issues (may be expected if data already exists)"
fi

# Start the application
echo "Starting Flask application..."
exec python app.py
