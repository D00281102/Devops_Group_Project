-- SCRUM-111: Combined ControlDB Schema
-- Compatible with Bright's SCRUM-108 authentication design

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Buildings and their creators
CREATE TABLE IF NOT EXISTS buildings (
    building_id SERIAL PRIMARY KEY,
    building_name VARCHAR(150) NOT NULL,
    building_code VARCHAR(64) NOT NULL UNIQUE,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Building memberships, roles and approval statuses
CREATE TABLE IF NOT EXISTS building_members (
    membership_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    building_id INTEGER NOT NULL REFERENCES buildings(building_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL DEFAULT 'member'
        CHECK (role IN ('admin', 'member')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, building_id)
);

-- Devices assigned to individual buildings
CREATE TABLE IF NOT EXISTS building_devices (
    device_id VARCHAR(100) PRIMARY KEY,
    building_id INTEGER NOT NULL REFERENCES buildings(building_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Improve device lookups by building
CREATE INDEX IF NOT EXISTS idx_building_devices_building
ON building_devices(building_id);


-- Link existing control settings to buildings
-- Keep building_id nullable to preserve the original settings row
ALTER TABLE control_settings
ADD COLUMN IF NOT EXISTS building_id INTEGER
REFERENCES buildings(building_id);

-- Allow only one settings record per building
CREATE UNIQUE INDEX IF NOT EXISTS unique_control_settings_building
ON control_settings(building_id);