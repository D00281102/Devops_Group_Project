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

wait_for_writable_database() {
    local deadline=$((SECONDS + 60))
    local writable

    while (( SECONDS < deadline )); do
        if writable="$(
            psql --no-psqlrc --dbname "$DB_NAME" \
                --tuples-only --no-align \
                --command="SELECT NOT pg_is_in_recovery()"
        )" && [ "$writable" = "t" ]; then
            return 0
        fi

        echo "PostgreSQL is not writable yet; waiting five seconds." >&2
        sleep 5
    done

    echo "PostgreSQL did not become writable within 60 seconds." >&2
    return 1
}

initialize_databases() {
    local existing_database

    wait_for_writable_database || return $?

    existing_database="$(
        psql --set=ON_ERROR_STOP=1 --dbname "$DB_NAME" \
            --tuples-only --no-align \
            --command="SELECT 1 FROM pg_database WHERE datname = '$CONTROL_DB_NAME'"
    )" || return $?

    if [ "$existing_database" != "1" ]; then
        createdb --maintenance-db "$DB_NAME" "$CONTROL_DB_NAME" || return $?
    fi

    psql --set=ON_ERROR_STOP=1 --dbname "$DB_NAME" \
        --file=/schema/telemetry.sql || return $?
    psql --set=ON_ERROR_STOP=1 --dbname "$CONTROL_DB_NAME" \
        --file=/schema/control_settings.sql || return $?
    psql --set=ON_ERROR_STOP=1 --dbname "$CONTROL_DB_NAME" \
        --file=/migrations/002_combined_control_db_schema.sql || return $?
}

for attempt in 1 2 3; do
    if initialize_databases; then
        exit 0
    fi

    if [ "$attempt" -eq 3 ]; then
        echo "Database initialization failed after three attempts." >&2
        exit 1
    fi

    echo "Database initialization attempt $attempt failed; retrying in five seconds." >&2
    sleep 5
done
