#!/bin/sh
set -e

# Install required tools.
# - rclone is needed for all flows (including pass-through commands)
# - postgresql-client is needed for backup (pg_dump) and automated restore (psql)
if ! command -v rclone >/dev/null 2>&1; then
	if command -v apk >/dev/null 2>&1; then
		echo "Installing rclone..."
		apk add -q --no-cache rclone >/dev/null
	else
		echo "rclone not found and no supported package manager available."
		exit 1
	fi
fi

if [ "$#" -eq 0 ] || [ "${1:-}" = "restore-db" ]; then
	if ! command -v pg_dump >/dev/null 2>&1 || ! command -v psql >/dev/null 2>&1; then
		if command -v apk >/dev/null 2>&1; then
			echo "Installing postgresql-client..."
			apk add -q --no-cache postgresql-client >/dev/null
		else
			echo "postgresql-client not found and no supported package manager available."
			exit 1
		fi
	fi
fi

RCLONE_PCLOUD_AUTH=$(cat /run/secrets/RCLONE_CONFIG_PCLOUD_AUTH)
RESTIC_REPOSITORY=$(cat /run/secrets/RESTIC_REPOSITORY)
export RESTIC_REPOSITORY

# Configure rclone for pCloud so both restic (rclone backend) and pass-through
# rclone commands work in all modes (backup, restore-db, manual commands).
mkdir -p /root/.config/rclone
cat > /root/.config/rclone/rclone.conf <<EOF
[pcloud]
type = pcloud
hostname = eapi.pcloud.com
token = $RCLONE_PCLOUD_AUTH
EOF
chmod 600 /root/.config/rclone/rclone.conf

if [ "${1:-}" = "help" ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	echo "Usage:"
	echo "  backup.sh                       # Create DB backup and apply retention policy"
	echo "  backup.sh restore-db [SNAPSHOT] [DB_NAME]"
	echo "                                  # Restore snapshot (default: latest) into DB (default: users_db)"
	echo "  backup.sh <any command>         # Pass-through command (e.g. restic snapshots)"
	exit 0
fi

if [ "${1:-}" = "restore-db" ]; then
	SNAPSHOT="${2:-latest}"
	DB_NAME="${3:-users_db}"
	RESTORE_DIR="/tmp/restic_restore_$(date +%Y%m%d_%H%M%S)"

	DB_USER=$(cat /run/secrets/DB_USER)
	DB_PASSWORD=$(cat /run/secrets/DB_PASSWORD)
	export PGPASSWORD="$DB_PASSWORD"

	echo "Restoring snapshot '$SNAPSHOT' to temporary directory..."
	mkdir -p "$RESTORE_DIR"
	restic restore "$SNAPSHOT" --target "$RESTORE_DIR"

	DUMP_FILE=$(find "$RESTORE_DIR" -type f -name "*.sql.gz" | sort | tail -n 1)
	if [ -z "$DUMP_FILE" ]; then
		echo "No .sql.gz dump found in restored snapshot."
		rm -rf "$RESTORE_DIR"
		exit 1
	fi

	echo "Recreating database '$DB_NAME'..."
	psql -h db -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 \
		-c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"
	psql -h db -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 \
		-c "DROP DATABASE IF EXISTS \"$DB_NAME\";"
	psql -h db -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 \
		-c "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\";"

	echo "Importing dump '$DUMP_FILE' into '$DB_NAME'..."
	# Newer pg_dump may emit SET transaction_timeout, unsupported on older servers.
	gunzip -c "$DUMP_FILE" \
		| sed '/^SET transaction_timeout =/d' \
		| psql -h db -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1

	rm -rf "$RESTORE_DIR"
	echo "Database restore completed successfully."
	exit 0
fi

# Pass-through mode for manual operations, for example:
# docker compose --profile backup run --rm backup restic init
# docker compose --profile backup run --rm backup rclone ls pcloud:/Backups/WebShop
if [ "$#" -gt 0 ]; then
	exec "$@"
fi

DATE=$(date +%Y%m%d_%H%M%S)
FILE="/tmp/db_$DATE.sql.gz"

DB_USER=$(cat /run/secrets/DB_USER)
DB_PASSWORD=$(cat /run/secrets/DB_PASSWORD)
export PGPASSWORD="$DB_PASSWORD"

echo "Dumping database..."

pg_dump -h db -U "$DB_USER" users_db | gzip > "$FILE"

echo "Running restic backup..."

restic backup "$FILE"

echo "Applying retention policy..."

restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune

rm "$FILE"

echo "Backup finished."