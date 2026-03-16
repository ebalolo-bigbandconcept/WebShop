#!/bin/sh
set -e

# Allow manual restic operations from docker compose run, for example:
# docker compose --profile backup run --rm backup restic init
if [ "$#" -gt 0 ]; then
	exec "$@"
fi

if ! command -v pg_dump >/dev/null 2>&1; then
	if command -v apk >/dev/null 2>&1; then
		apk add --no-cache postgresql-client >/dev/null
	else
		echo "pg_dump not found and no supported package manager available."
		exit 1
	fi
fi

DATE=$(date +%Y%m%d_%H%M%S)
FILE="/tmp/db_$DATE.sql.gz"

DB_USER=$(cat /run/secrets/DB_USER)
DB_PASSWORD=$(cat /run/secrets/DB_PASSWORD)

echo "Dumping database..."

pg_dump -h db -U "$DB_USER" users_db | gzip > "$FILE"

echo "Running restic backup..."

restic backup "$FILE"

echo "Applying retention policy..."

restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune

rm "$FILE"

echo "Backup finished."