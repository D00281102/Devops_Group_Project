
-- SCRUM-108: User Login and Multi-Building Database Schema

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Buildings
CREATE TABLE IF NOT EXISTS buildings (
    building_id SERIAL PRIMARY KEY,
    building_name VARCHAR(150) NOT NULL,
    building_code VARCHAR(64) UNIQUE NOT NULL,
    created_by INTEGER NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Building memberships
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

-- 4. Building devices
CREATE TABLE IF NOT EXISTS building_devices (
    device_id VARCHAR(100) PRIMARY KEY,
    building_id INTEGER NOT NULL REFERENCES buildings(building_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Add building relationship to existing control settings
ALTER TABLE control_settings
ADD COLUMN IF NOT EXISTS building_id INTEGER
REFERENCES buildings(building_id) ON DELETE CASCADE;

-- One settings record per building
CREATE UNIQUE INDEX IF NOT EXISTS idx_control_settings_building
ON control_settings(building_id)
WHERE building_id IS NOT NULL;

-- 6. Useful indexes
CREATE INDEX IF NOT EXISTS idx_building_members_user
ON building_members(user_id);

CREATE INDEX IF NOT EXISTS idx_building_members_building
ON building_members(building_id);

CREATE INDEX IF NOT EXISTS idx_building_members_status
ON building_members(status);

CREATE INDEX IF NOT EXISTS idx_building_devices_building
ON building_devices(building_id);
