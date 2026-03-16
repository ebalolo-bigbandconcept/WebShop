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

# Install rclone if not present (needed for webdav/pcloud backend)
if ! command -v rclone >/dev/null 2>&1; then
	if command -v apk >/dev/null 2>&1; then
		apk add --no-cache rclone >/dev/null
	else
		echo "rclone not found and no supported package manager available."
		exit 1
	fi
fi

DATE=$(date +%Y%m%d_%H%M%S)
FILE="/tmp/db_$DATE.sql.gz"

DB_USER=$(cat /run/secrets/DB_USER)
DB_PASSWORD=$(cat /run/secrets/DB_PASSWORD)

# RESTIC_REPOSITORY secret contains a webdav:// URL for pcloud.
# Restic does not natively support webdav; we configure rclone as the backend.
WEBDAV_URL=$(cat /run/secrets/RESTIC_REPOSITORY)

# Extract user:password from the URL (scheme://user:pass@host/path)
# Expected format: webdav://user@host/path  (password via RESTIC_PASSWORD secret)
WEBDAV_USER=$(echo "$WEBDAV_URL" | sed 's|webdav://||' | sed 's|@.*||')
WEBDAV_HOST=$(echo "$WEBDAV_URL" | sed 's|webdav://[^@]*@||' | sed 's|/.*||')
WEBDAV_ROOT=$(echo "$WEBDAV_URL" | sed "s|webdav://[^/]*/||")
WEBDAV_PASS=$(cat /run/secrets/RESTIC_PASSWORD)

mkdir -p /root/.config/rclone
cat > /root/.config/rclone/rclone.conf <<EOF
[pcloud]
type = webdav
url = https://${WEBDAV_HOST}
vendor = other
user = ${WEBDAV_USER}
pass = $(rclone obscure "$WEBDAV_PASS")
EOF

export RESTIC_REPOSITORY="rclone:pcloud:${WEBDAV_ROOT}"
export RESTIC_PASSWORD_FILE=/run/secrets/RESTIC_PASSWORD

echo "Dumping database..."

pg_dump -h db -U "$DB_USER" users_db | gzip > "$FILE"

echo "Running restic backup..."

restic backup "$FILE"

echo "Applying retention policy..."

restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune

rm "$FILE"

echo "Backup finished."