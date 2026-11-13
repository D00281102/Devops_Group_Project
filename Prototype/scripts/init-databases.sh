#!/usr/bin/env bash
set -Eeuo pipefail

: "${DB_NAME:?DB_NAME must be set}"
: "${CONTROL_DB_NAME:?CONTROL_DB_NAME must be set}"

if ! [[ "$DB_NAME" =~ ^[a-zA-Z_][a-zA-Z0-9_-]{0,62}$ ]] ||
    ! [[ "$CONTROL_DB_NAME" =~ ^[a-zA-Z_][a-zA-Z0-9_-]{0,62}$ ]]; then
    echo "Database names may contain only letters, digits, underscores, and hyphens." >&2
    exit 1
fi

if [ "$DB_NAME" = "$CONTROL_DB_NAME" ]; then
    echo "DB_NAME and CONTROL_DB_NAME must refer to different databases." >&2
    exit 1
fi

existing_database="$(
    psql --dbname "$DB_NAME" \
        --tuples-only --no-align \
        --command="SELECT 1 FROM pg_database WHERE datname = '$CONTROL_DB_NAME'"
)"

if [ "$existing_database" != "1" ]; then
    createdb --maintenance-db "$DB_NAME" "$CONTROL_DB_NAME"
fi

psql --set=ON_ERROR_STOP=1 --dbname "$DB_NAME" \
    --file=/schema/telemetry.sql
psql --set=ON_ERROR_STOP=1 --dbname "$CONTROL_DB_NAME" \
    --file=/schema/control_settings.sql
psql --set=ON_ERROR_STOP=1 --dbname "$CONTROL_DB_NAME" \
    --file=/migrations/002_combined_control_db_schema.sql
