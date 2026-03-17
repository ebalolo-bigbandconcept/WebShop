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

# Heal inconsistent Alembic state on fresh/empty databases where
# alembic_version is set but application tables were never created.
echo "Checking database schema consistency..."
python - <<'PY'
import os
from sqlalchemy import create_engine, inspect, text

database_url = os.environ.get("DATABASE_URL")
if not database_url:
  print("DATABASE_URL not set, skipping consistency check.")
  raise SystemExit(0)

engine = create_engine(database_url)

with engine.connect() as conn:
  inspector = inspect(conn)
  tables = set(inspector.get_table_names(schema="public"))

  if "users" in tables:
    print("Database schema looks consistent (users table found).")
    raise SystemExit(0)

  # If alembic metadata exists alone, reset it so upgrade can replay from base.
  if tables == {"alembic_version"}:
    print(
      "Detected inconsistent schema: only alembic_version table exists. "
      "Resetting alembic_version to replay migrations."
    )
    conn.execute(text("DELETE FROM alembic_version"))
    conn.commit()
  else:
    print(
      "Schema check warning: users table missing but schema is not empty. "
      "Proceeding with migrations."
    )
PY

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
