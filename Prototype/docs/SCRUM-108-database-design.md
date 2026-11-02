# SCRUM-108 – Database Design for User Login and Multiple Buildings

## 1. Introduction

This document describes the proposed database changes required to support individual user accounts and multiple buildings in the project.

The existing `control_settings_db` will be extended to support user accounts, building management and membership approval.

The telemetry database will remain separate.

## 2. Proposed Database Tables

### users
Stores individual user accounts.

- user_id – Primary key
- full_name – User's full name
- email – Unique email address
- password_hash – Securely hashed password
- created_at – Account creation date

### buildings
Stores information about each building.

- building_id – Primary key
- building_name – Name of the building
- building_code – Unique code used to request access
- created_by – User who created the building
- created_at – Building creation date

### building_members
Connects users to buildings.

- membership_id – Primary key
- user_id – Foreign key referencing users
- building_id – Foreign key referencing buildings
- role – Admin or member
- status – Pending, approved or rejected
- joined_at – Membership creation date

A user can belong to multiple buildings, and each building can have multiple users.

### control_settings
Stores control settings for individual buildings.

The existing table will be extended with a `building_id` foreign key so each building can have its own temperature, humidity and lighting settings.

## 3. Membership Rules

- A user who creates a building automatically becomes its administrator.
- Users can request to join an existing building using its building code.
- Join requests require approval from the building administrator.
- Only approved members can access their building's data.
- Administrators can approve or reject membership requests.

## 4. Database Separation

The existing `control_settings_db` will store users, buildings, memberships and control settings.

The telemetry database will remain separate.

The relationship between sensor devices, buildings and telemetry records requires further integration planning with the team.

## 5. Implementation Status

The proposed database schema has been created and tested using a separate PostgreSQL Docker test database.

The tests covered user creation, building creation, membership relationships, building-specific control settings and database constraints.

The original global control settings record was preserved during testing.

The schema has not yet been applied to the team's shared ControlDB.

## 6. Existing Control API Findings

The existing FastAPI application currently provides two control settings endpoints:

- GET `/control-settings` retrieves the saved control settings.
- PUT `/control-settings` updates the saved control settings.

Both endpoints currently operate on a single record using `id = 1`.

The existing ControlSettings model contains temperature_threshold, humidity_threshold, light_enabled and updated_at.

This means the current implementation supports one shared set of control settings rather than separate settings for different buildings.

## 7. Required Changes

The control settings implementation will need to support a building_id so that each building can have its own settings.

The API will also need authentication and membership checks to ensure users can only access buildings they belong to.

The existing telemetry and control functionality should be preserved while these changes are introduced.

## 8. Existing Control Logic Findings

The existing Control Logic retrieves control settings from PostgreSQL using the get_control_settings() function.

The function currently queries the control_settings table using `WHERE id = 1`.

The retrieved settings are used when processing database sensor readings and incoming MQTT messages.

This confirms that the current automated control system also relies on one shared settings record.

## 9. Required Control Logic Changes

The Control Logic will need to identify the building associated with each sensor before retrieving its control settings.

The telemetry implementation currently does not expose a building_id field. The relationship between sensor devices and buildings therefore needs to be agreed with the team before implementing building-specific automated control.

Existing MQTT communication and actuator functionality must be preserved.

## 10. Existing Telemetry API Findings

The existing telemetry API provides GET, POST, PUT and DELETE endpoints for sensor records.

The telemetry records contain the following fields:

- records
- ts
- device
- co
- humidity
- light
- lpg
- motion
- smoke
- temp

The existing telemetry implementation uses the device field to identify sensor devices.

There is currently no building_id field in the telemetry model or database queries.

## 11. Proposed Sensor and Building Relationship

A building_devices table is proposed in the ControlDB.

This table will associate registered sensor devices with their respective buildings using device identifiers and building_id.

The telemetry database will remain separate.

The integration between the device registry, telemetry records and Control Logic must be agreed and tested before implementing building-specific automated control.

## 12. Overall Investigation Summary

The existing system currently uses one shared control settings record.

The investigation identified the following changes required for SCRUM-108:

1. Introduce individual user accounts.
2. Introduce building management.
3. Support multiple buildings per user.
4. Introduce membership roles and approval statuses.
5. Associate control settings with individual buildings.
6. Associate sensor devices with buildings.
7. Introduce authenticated and building-scoped API access.
8. Update Control Logic to retrieve the correct building settings.

The proposed schema changes were applied only to an isolated PostgreSQL test database. The team's shared ControlDB and telemetry database have not been modified.

## 13. Database Migration Considerations

The existing control_settings table contains a global settings record.

The proposed migration extends the existing table with a building_id column while preserving the original record.

This was tested successfully in an isolated PostgreSQL database. The original record remained available with a NULL building_id, while separate settings records were created for Building A and Building B.

The schema must be applied after the ControlDB initialization script has created the existing control_settings table.

The global settings functionality will only be retired after the building-specific API and Control Logic have been implemented and tested.

The team's shared database has not been modified.

## 14. Implementation Safety

- Existing telemetry data must remain untouched.
- Existing database initialization must be preserved.
- The new tables must use appropriate primary and foreign keys.
- User passwords must never be stored as plain text.
- Building membership must be checked by the API.
- Database changes must be tested before integration into the team's shared environment.