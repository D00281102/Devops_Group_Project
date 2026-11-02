

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



A unique index on `control_settings.building_id` prevents a building from having multiple settings records.



## Database Constraints



The combined schema includes:



- Primary keys for users, buildings, memberships, devices and control settings.

- Foreign keys linking buildings to creators and linking memberships, devices and settings to buildings.

- Unique email addresses and building joining codes.

- Unique user-building memberships.

- Membership roles restricted to `admin` and `member`.

- Membership statuses restricted to `pending`, `approved` and `rejected`.

- A unique index enforcing one control settings record per building.



## Running the Database Migration



The combined SQL migration is located at:



`Prototype/migrations/002_combined_control_db_schema.sql`



It extends the existing database without deleting the original settings records.



The schema is currently committed to the SCRUM-111 feature branch and has been tested in a separate database.



\*\*Do not apply the migration to the main `control_settings_db` until it has been reviewed and approved by the team.\*\*



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



The migration produced:



```text

CREATE TABLE

CREATE TABLE

CREATE TABLE

CREATE TABLE

CREATE INDEX

ALTER TABLE

CREATE INDEX

```



The migration was also executed a second time without errors. Existing tables, columns and indexes were skipped.



\*\*Important:\*\* This migration expects an existing `control_settings` table. A fresh test database needs that original table before running the migration.



## Testing Results



The following tests were successfully completed using `controldb_combined_test`.



| Test | Result |

|---|---|

| Create all five database tables | Passed |

| Preserve existing control settings | Passed |

| Create a user account | Passed |

| Create a building linked to its creator | Passed |

| Assign an approved admin membership | Passed |

| Assign an IoT device to a building | Passed |

| Create building-specific control settings | Passed |

| Prevent duplicate settings for a building | Passed |

| Reject settings referencing nonexistent buildings | Passed |

| Verify membership constraints | Passed |

| Run the migration multiple times | Passed |



### Original Settings Preservation



The following records were verified after applying the migration:



| Settings ID | Building ID | Temperature | Humidity | Light |

|---|---|---|---|---|

| 1 | NULL | 28 | 70 | ON |

| 2 | 1 | 25 | 65 | ON |



The original settings record remained unchanged and was not automatically assigned to a building.



The second record demonstrates that Building 1 can have independent control settings.



### Test Database Record Counts



The final test database contained:



| Table | Records |

|---|---|

| `users` | 1 |

| `buildings` | 1 |

| `building_members` | 1 |

| `building_devices` | 1 |

| `control_settings` | 2 |



Additional tests of multi-building memberships, pending approvals and membership restrictions were performed against the earlier `controldb_test` schema. Those tests should be repeated against the combined schema as needed before final integration.



## Security Considerations



### Password Storage



The `users` table contains a `password_hash` field.



User passwords must be securely hashed by the authentication API before they are stored in ControlDB.



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



Bright's authentication API uses the agreed `users` structure containing:



- `user_id`

- `full_name`

- `email`

- `password_hash`



The API will interact with the membership and building tables to manage user access.



Full authentication and integration testing against this combined database schema is still required.



### Liam — Control Logic



Liam's Control Logic will use `building_id` to identify the relevant building and retrieve its control settings.



Example lookup:



```sql

SELECT temperature_threshold, humidity_threshold, light_enabled

FROM control_settings

WHERE building_id = 1;

```



The existing Control Logic currently uses the legacy settings record (`id = 1`). Updating that behaviour is part of the multi-building integration work.



### Daniils — MQTT and Device Integration



The `building_devices` table allows devices to be associated with specific buildings.



This supports identifying which building a sensor belongs to when processing IoT data.



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

4. Complete remaining membership, authentication and integration tests.

5. Review the migration against any schema changes already introduced by teammates.

6. Apply the approved migration safely and verify the existing data remains intact.



## Git and Jira



\*\*Jira task:\*\* SCRUM-111 — ControlDB Accounts, Passwords and More Values



\*\*Feature branch:\*\*



`feature/SCRUM-111-simon-control-accounts`



\*\*Combined schema commit:\*\*



`99afeb3`



The combined SQL migration has been committed and pushed to the SCRUM-111 feature branch.



The migration has not yet been applied to the main ControlDB.



The database backup, local environment credentials and temporary files must not be accidentally committed.



