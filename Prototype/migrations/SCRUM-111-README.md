
# SCRUM-111 — ControlDB Expansion

## Overview

This task expands the existing PostgreSQL ControlDB to support user accounts, secure password-hash storage, multiple buildings, building memberships, device assignments and building-specific control settings.

The database is named `control_settings_db` and remains separate from the telemetry database.

The combined schema was developed alongside Bright's SCRUM-108 database design to maintain compatibility with the authentication API.

## Database Tables

The expanded database contains five main tables:

1. `users` — Stores user IDs, full names, email addresses, password hashes and account creation timestamps.
2. `buildings` — Stores building IDs, building names, unique joining codes, creator IDs and creation timestamps.
3. `building_members` — Links users to buildings, including admin/member roles and membership approval statuses.
4. `building_devices` — Links IoT devices to their assigned buildings.
5. `control_settings` — Stores temperature, humidity and lighting settings, with an optional building relationship.

## Database Relationships

- Each user has a unique `user_id` and can belong to multiple buildings.
- Each building has a unique `building_id` and references its creator through `created_by`.
- `building_members` connects users to buildings and stores their role (`admin` or `member`) and approval status (`pending`, `approved` or `rejected`).
- `building_devices` connects each device to a building using `building_id`.
- `control_settings` supports separate temperature, humidity and lighting settings for individual buildings.

The existing `control_settings` record with `id = 1` is preserved with `building_id = NULL` until the team agrees on its default building assignment.

A unique index on `control_settings.building_id` prevents a building from having multiple settings records. PostgreSQL permits multiple `NULL` values in this unique index, so legacy unassigned records are not automatically restricted to one.

## Database Constraints

The combined schema includes:

- Primary keys for users, buildings, memberships, devices and control settings.
- Foreign keys linking buildings to creators and linking memberships, devices and settings to buildings.
- Unique email addresses and building joining codes.
- Unique user-building memberships.
- Membership roles restricted to `admin` and `member`.
- Membership statuses restricted to `pending`, `approved` and `rejected`.
- A unique index enforcing one control settings record per non-NULL building ID.

## Running the Database Migration

The combined SQL migration is located at:

`Prototype/migrations/002_combined_control_db_schema.sql`

It extends the existing database without deleting the original settings records.

The schema is committed to the SCRUM-111 feature branch and has been tested in a separate database.

**Do not apply the migration to the main `control_settings_db` until it has been reviewed and approved by the team.**

### Testing the Migration

The migration was successfully tested in a separate PostgreSQL database called `controldb_combined_test`.

The following commands are run from the project root.

#### 1. Copy the migration into Docker

```cmd
docker cp Prototype\migrations\002_combined_control_db_schema.sql devops_group_project-control-db-1:/tmp/002_combined_control_db_schema.sql
```

#### 2. Execute the migration against the test database

```cmd
docker exec devops_group_project-control-db-1 psql -X -v ON_ERROR_STOP=1 -1 -U postgres -d controldb_combined_test -f /tmp/002_combined_control_db_schema.sql
```

The `-1` option runs the migration in a single transaction, while `ON_ERROR_STOP=1` stops execution if an SQL error occurs.

The initial migration produced:

```text
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE TABLE
CREATE INDEX
ALTER TABLE
CREATE INDEX
```

The migration was also executed again without errors. Existing tables, columns and indexes were skipped.

**Important:** This migration expects an existing `control_settings` table. A fresh test database needs the original table before running the migration.

`IF NOT EXISTS` prevents duplicate-object errors but does not verify that existing table definitions match the intended schema.

## Testing Results

The following database-level tests were completed against `controldb_combined_test`.

| Test | Result |
|---|---|
| Create all five database tables | Passed |
| Preserve existing control settings | Passed |
| Create test users and buildings | Passed |
| Assign an approved admin membership | Passed |
| Assign an IoT device to a building | Passed |
| Create building-specific control settings | Passed |
| Reject duplicate settings for one building | Passed |
| Reject nonexistent building references in settings | Passed |
| Allow one user to belong to multiple buildings | Passed |
| Reject duplicate user-building memberships | Passed |
| Reject invalid membership role (`superadmin`) | Passed |
| Reject invalid approval status (`suspended`) | Passed |
| Preserve memberships after failed updates | Passed |
| Assign default role `member` and status `pending` | Passed |
| Update membership from `pending` to `approved` | Passed |
| Store independent settings for two buildings | Passed |
| Run the migration multiple times | Passed |

### Multi-Building Membership Test

Test Admin (`user_id = 1`) was successfully assigned to two buildings.

| User ID | Building ID | Role | Status |
|---|---|---|---|
| 1 | 1 | admin | approved |
| 1 | 2 | admin | approved |

An attempt to add a duplicate membership for user `1` and building `2` was rejected by:

`building_members_user_id_building_id_key`

Invalid values were also rejected by the following constraints:

- `building_members_role_check` — rejected `superadmin`.
- `building_members_status_check` — rejected `suspended`.

After the failed operations, both original admin memberships remained unchanged.

### Membership Approval Test

A second test account was created:

- User ID: `2`
- Name: `Test Member`
- Email: `member-test@example.com`

A membership was created for Building 1 without specifying the role or status.

PostgreSQL automatically assigned:

```text
membership_id = 5
user_id = 2
building_id = 1
role = member
status = pending
```

The membership was subsequently updated to `approved`.

```text
membership_id = 5
user_id = 2
building_id = 1
role = member
status = approved
```

**Note:** This verifies database storage and updates. It does not prove that only authorised building admins can approve requests. That behaviour must be enforced and tested in Bright's API.

### Original Settings Preservation

The following settings were verified after applying the migration and completing the multi-building tests:

| Settings ID | Building ID | Temperature | Humidity | Light |
|---|---|---|---|---|
| 1 | NULL | 28 | 70 | ON |
| 2 | 1 | 25 | 65 | ON |
| 5 | 2 | 22 | 60 | OFF |

The original settings record remained unchanged and was not automatically assigned to a building.

Building 1 and Building 2 have independent temperature, humidity and lighting settings.

The latest output was saved locally to:

`Prototype/migrations/SCRUM-111-test-results.txt`

### Test Database Record Counts

After completing the tests, the expected records are:

| Table | Records |
|---|---|
| `users` | 2 |
| `buildings` | 2 |
| `building_members` | 3 |
| `building_devices` | 1 |
| `control_settings` | 3 |

These counts reflect the test records created and verified during this testing sequence. They are not production database counts.

Earlier tests were also performed against `controldb_test`, which used a previous schema design. The combined-schema results above are the relevant evidence for SCRUM-111.

## Security Considerations

### Password Storage

The `users` table contains a `password_hash` field.

User passwords must be securely hashed by the authentication API before storage, using an appropriate password-hashing algorithm.

Passwords must never be stored as plain text.

During database testing, `TEST_HASH_NOT_REAL` was used as a placeholder. This value is not a real password hash and must not be used for actual accounts.

### Building Access

The database supports:

- Users belonging to multiple buildings.
- Separate admin/member roles for each building.
- Pending, approved and rejected membership statuses.
- Device assignments to specific buildings.

The API must enforce authentication and authorisation when allowing users to access settings, approve memberships or manage buildings.

Database relationships alone do not enforce API-level permissions.

### Building Joining Codes

Each building has a unique `building_code`.

Joining codes must be generated securely and checked by the API. Access should only be granted after the appropriate approval process.

The current schema stores building codes as text; secure generation and protection of these codes require application-level implementation.

## Application Integration

### Bright — Authentication and Control API

The combined schema uses the agreed `users` columns:

- `user_id`
- `full_name`
- `email`
- `password_hash`

The authentication API is responsible for password hashing, registration, login and enforcing building access permissions.

The expected workflow is:

1. A user registers or logs in.
2. A user creates a building or requests to join an existing building.
3. A building creator receives an approved admin membership through the API workflow.
4. A joining user receives a pending membership.
5. An authorised admin approves or rejects the request.
6. Approved members access their building's permitted functionality.

The database supports this workflow, but complete authentication and authorisation integration testing against the combined schema is still pending.

### Liam — Control Logic

Liam's Control Logic will need to use `building_id` to identify the appropriate building and retrieve its control settings.

Example lookup:

```sql
SELECT temperature_threshold, humidity_threshold, light_enabled
FROM control_settings
WHERE building_id = 1;
```

The existing Control Logic currently uses the legacy settings record (`id = 1`). Updating that behaviour is part of the multi-building integration work.

**Liam's Control Logic source file was not modified as part of SCRUM-111.**

### Daniils — MQTT and Device Integration

The `building_devices` table associates device IDs with individual buildings.

This supports identifying the appropriate building when handling IoT device data.

The end-to-end device and messaging integration has not yet been verified against this expanded database schema.

## ControlDB Connection Details

When running inside Docker:

| Setting | Value |
|---|---|
| Host | `control-db` |
| Port | `5432` |
| Database | `control_settings_db` |
| User | `postgres` |
| Password | Configured using `CONTROL_DB_PASSWORD` |

For local Windows connections, the ControlDB Docker container exposes PostgreSQL on port `5435`.

Database credentials must be kept in environment configuration and never committed to Git.

## Remaining Work

Before applying the combined schema to the main database:

1. Complete Bright's review of the combined SQL schema.
2. Confirm compatibility with the authentication API.
3. Confirm how the existing unassigned settings record should be handled.
4. Test authentication, admin authorisation and membership approval through the actual API.
5. Verify multi-building settings retrieval through the Control API and Control Logic.
6. Review the migration against any schema changes already introduced by teammates.
7. Apply the approved migration safely and verify existing data remains intact.
8. Complete an end-to-end team demo after the services are integrated.

## Git and Jira

**Jira task:** SCRUM-111 — ControlDB Accounts, Passwords and More Values

**Feature branch:**

`feature/SCRUM-111-simon-control-accounts`

**Combined schema commit:**

`99afeb3`

**Initial documentation commit:**

`ba79396`

**Pull request:**

[PR #28 — Expand ControlDB for Users, Buildings and Settings](https://github.com/D00281102/Devops_Group_Project/pull/28)

The combined SQL migration and initial documentation have been committed and pushed to the SCRUM-111 feature branch.

This document records the additional database tests completed afterward.

The migration has not yet been applied to the main ControlDB.

The database backup, local environment credentials and temporary files must not be accidentally committed.
