SELECT 'CREATE DATABASE control_settings_db'
WHERE NOT EXISTS (
    SELECT FROM pg_database
    WHERE datname = 'control_settings_db'
)
\gexec

\c control_settings_db

CREATE TABLE IF NOT EXISTS control_settings (
    id SERIAL PRIMARY KEY,
    temperature_threshold DOUBLE PRECISION NOT NULL,
    humidity_threshold DOUBLE PRECISION NOT NULL,
    light_enabled BOOLEAN NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO control_settings (
    temperature_threshold,
    humidity_threshold,
    light_enabled
)
SELECT
    25,
    70,
    TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM control_settings
);