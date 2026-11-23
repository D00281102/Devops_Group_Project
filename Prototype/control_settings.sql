CREATE TABLE IF NOT EXISTS control_settings (
    id SMALLINT PRIMARY KEY CHECK (id = 1),

    temperature_threshold DOUBLE PRECISION NOT NULL DEFAULT 25.0
        CHECK (temperature_threshold BETWEEN -50 AND 100),

    humidity_threshold DOUBLE PRECISION NOT NULL DEFAULT 70.0
        CHECK (humidity_threshold BETWEEN 0 AND 100),

    light_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO control_settings (id)
VALUES (1)
ON CONFLICT (id) DO NOTHING;