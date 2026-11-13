# Containerised IoT and Kafka Setup

<<<<<<< HEAD
> **Purpose:** Docker Compose setup, MQTT/Kafka integration, control API, authentication, database design and multi-building test evidence. For Windows/Python manual development see [`local-setup.md`](local-setup.md).
>
> **Version note:** This guide preserves work from different development dates. Historical configuration must be checked against the current `docker-compose.yml`, API routes and SQL schema. Do not commit `.env` files, passwords or JWT signing secrets.

## Quick navigation

- Historical hybrid Windows/Docker Kafka startup: **Start the Kafka Services Automatically**
- Containerised sensor, broker, control logic and actuator: **Dockerised IoT Control System**
- Control API service: **Control API**
- Registration, login and JWT: **User Authentication API (SCRUM-140)**
- Proposed database structure and migration safety: **SCRUM-108**
- Mocked multi-building isolation results and limitations: **SCRUM-122**

This guide covers the project's Docker Compose setup, including Kafka, Kafka Connect, Kafka UI, Mosquitto MQTT, the Sensor Simulator, Control Logic, Actuator Simulator and Grafana.

**Note:** The original Kafka setup instructions below describe the earlier Windows-based configuration, where Mosquitto and the Sensor Simulator ran outside Docker. These instructions are retained for reference and may not match the current Compose configuration.
=======
This guide covers the project's Docker Compose setup, including PostgreSQL
with a persistent data volume, Kafka, Kafka Connect, Kafka UI, Mosquitto,
the Sensor Simulator, Control Logic, Actuator Simulator, the Control API,
and Grafana. The Windows-hosted Kafka consumer can also write telemetry to
the PostgreSQL container through the published host port.

**Note:** The Kafka section below includes the earlier Windows-based Kafka
Connect plugin setup. The current Compose stack runs Mosquitto and the
Sensor Simulator in Docker; Kafka Connect loads its MQTT plugin from the
configured host plugin directory.
>>>>>>> main

For the current containerised Sensor Simulator, Control Logic, Actuator Simulator and Mosquitto setup, see **Dockerised IoT Control System — SCRUM-102** further down this document.

For the original manual Windows setup, see [local-setup.md](local-setup.md).

## Architecture
```text
<<<<<<< HEAD

Data_Sensor.py

    |

    | MQTT: localhost:1883

    v

Mosquitto on Windows

    |

    | MQTT source connector

    v

=======
Sensor Simulator (Docker) or Data_Sensor.py (Windows)
    |
    | MQTT: mosquitto:1883 (Docker) or localhost:1883 (Windows)
    v
Mosquitto in Docker
    |
    | MQTT source connector via host.docker.internal:1883
    v
>>>>>>> main
Kafka Connect in Docker

    |

    | Kafka: localhost:9092

    v

Kafka in Docker
<<<<<<< HEAD

    |

    +--> Kafka UI in Docker: http://localhost:8080

    |

    +--> Kafka consumer on Windows

=======
    |
    +--> Kafka UI in Docker: http://localhost:8081
    |
    +--> Database consumer on Windows
              |
              v
        PostgreSQL in Docker
        (`iot_telemetry_data`, persistent volume)
>>>>>>> main
```

## Prerequisites
Install and start:

- Docker Desktop

- Python 3
<<<<<<< HEAD

- Eclipse Mosquitto installed at `C:\Program Files\mosquitto`

=======
>>>>>>> main
- Apache Kafka tools installed at `C:\kafka`

Mosquitto does not need to be installed or started separately. Compose runs
it using the configuration file at:

```text

Prototype/mosquitto.conf

```

The dataset must be located at:

```text

Prototype/data/iot_telemetry_data.csv

```

Install the Python dependency:

```powershell

py -m pip install -r Prototype/requirements.txt

```

## Move the existing database into Docker

Back up the existing local PostgreSQL database before stopping it. Run from
the repository root while local PostgreSQL is running:

```powershell
New-Item -ItemType Directory -Force .\Prototype\data
pg_dump -h localhost -p 5434 -U postgres -d postgres --no-owner --no-acl -f .\Prototype\data\telemetry-backup.sql
```

The backup path is gitignored because it contains database data. If local
PostgreSQL occupies port 5434, stop its Windows service after creating the
backup. For PostgreSQL 17, run Administrator PowerShell:

```powershell
Stop-Service postgresql-x64-17
```

Start the PostgreSQL container with the credentials from `Prototype/.env`:

```powershell
docker compose --env-file Prototype/.env up -d postgres
```

Wait for `docker compose --env-file Prototype/.env ps postgres` to show the
container as healthy.

Restore the backup into the container:

```powershell
psql -h localhost -p 5434 -U postgres -d postgres -v ON_ERROR_STOP=1 -f .\Prototype\data\telemetry-backup.sql
```

The compose service keeps the database in the `postgres_data` named volume.
Restarting or running `docker compose --env-file Prototype/.env down`
preserves the data. Avoid `docker compose --env-file Prototype/.env down -v`,
which deletes that volume.

## Network Addresses
Windows applications use the ports:

```text

Kafka: localhost:9092

MQTT: localhost:1883

Kafka Connect REST API: localhost:8083
<<<<<<< HEAD

Kafka UI: http://localhost:8080

=======
Kafka UI: http://localhost:8081
>>>>>>> main
```

Docker containers use these internal addresses:

```text

Kafka: kafka:9093

MQTT from Kafka Connect: host.docker.internal:1883

```

Kafka UI is configured to use `kafka:9093` in `docker-compose.yml`.
The Windows API and database consumer connect to PostgreSQL at
`localhost:5434`, as configured in `Prototype/.env`. Other Docker services
can connect to PostgreSQL using `postgres:5432`.

## Start the Kafka Services Automatically
From the project root:

The Kafka startup script starts PostgreSQL, Mosquitto, Kafka, Kafka UI,
Kafka Connect, the Kafka topic, the MQTT connector, and a Python consumer
that writes records into the same PostgreSQL
`iot_telemetry_data` table. The consumer uses the `Prototype/.env` settings
shared with the API. Mosquitto uses the project's `Prototype/mosquitto.conf`
configuration so Kafka Connect running in Docker can connect to the MQTT
broker.

Run it from the project root:

```powershell
<<<<<<< HEAD

Set-Location "C:\Devops_Group_Project" (This is to set your directory)

=======
Set-Location "C:\Devops_Group_Project"
>>>>>>> main
py .\Prototype\scripts\start_kafka.py

```

Leave this terminal running; it remains attached to the database consumer.
Start the sensor in another terminal using the command in **Start the Sensor**.

Check the containers:

```powershell
<<<<<<< HEAD

docker compose ps

=======
docker compose --env-file Prototype/.env ps
>>>>>>> main
```

Follow Kafka logs if needed:

```powershell
<<<<<<< HEAD

docker compose logs -f kafka

=======
docker compose --env-file Prototype/.env logs -f kafka
>>>>>>> main
```

Verify that Kafka is reachable from Windows:

```powershell

Test-NetConnection localhost -Port 9092

```

The result should contain:

```text

TcpTestSucceeded : True

```

Open Kafka UI at:

```text
<<<<<<< HEAD

http://localhost:8080

=======
http://localhost:8081
>>>>>>> main
```

The script waits for Kafka before creating `sensor-telemetry`. It also waits for Kafka Connect before registering the MQTT source connector.

Check the running services:

```powershell
<<<<<<< HEAD

docker compose ps

=======
docker compose --env-file Prototype/.env ps
>>>>>>> main
```

Check Kafka Connect:

```powershell

Invoke-RestMethod http://localhost:8083/

```

Check that the MQTT connector is loaded:

```powershell

Invoke-RestMethod http://localhost:8083/connector-plugins

```

The response should show:

```text

io.confluent.connect.mqtt.MqttSourceConnector

```

Check the connector status:

```powershell

Invoke-RestMethod http://localhost:8083/connectors/mqtt-source/status

```

The connector and task should both report `RUNNING`.

## MQTT Subscriber (Optional)
Mosquitto is started automatically by `start_kafka.py`, so it does not need to be started manually.

To monitor the MQTT sensor messages in a separate terminal, run:

```powershell

& "C:\Program Files\mosquitto\mosquitto_sub.exe" `

 -h localhost `

 -p 1883 `

 -t sensors/telemetry `

 -v

```

## Start the Sensor
```powershell

Set-Location "C:\Devops_Group_Project"

py .\Prototype\Data_Sensor.py

```

The sensor publishes to `localhost:1883`, which Compose publishes from the
Docker Mosquitto container to Windows.

## View Data in Kafka UI
<<<<<<< HEAD
1. Open `http://localhost:8080`.

=======

1. Open `http://localhost:8081`.
>>>>>>> main
2. Select the `local` cluster.

3. Open the `sensor-telemetry` topic.

4. Select the `Messages` tab.

5. Set the value format to `String` or `UTF-8`.

6. Refresh the messages.

The topic should contain the JSON sensor records.

## Stop the Setup
Stop the Windows processes with `Ctrl+C`, then stop Docker services:

```powershell
<<<<<<< HEAD

docker compose down

=======
docker compose --env-file Prototype/.env down
>>>>>>> main
```

This stops containers but preserves the PostgreSQL volume and its data. Do
not use `docker compose --env-file Prototype/.env down -v` unless you
intentionally want to delete the database volume and stored Kafka data.

## Previous Setup Scope (Historical)
<<<<<<< HEAD
The current Compose file containerizes Kafka and Kafka UI only. A fully containerized setup would also need Compose services for Mosquitto, Kafka Connect, the MQTT connector plugin, the sensor, and the Kafka consumer.

## Dockerised IoT Control System — 21/10/26 updated
### Overview
=======

The current Compose file runs PostgreSQL, Kafka, Kafka UI, Kafka Connect,
Mosquitto, Grafana, and the IoT control components in Docker. The Windows
Kafka consumer remains a separate process and connects to PostgreSQL using
`Prototype/.env`.

## Dockerised IoT Control System — 21/10/26 updated

### Overview

>>>>>>> main
The IoT control components have been containerised using Docker Compose. The system reads sensor data from a CSV file, publishes readings through MQTT, evaluates configurable control rules and sends commands to an actuator simulator.

The relevant services are:

- `mosquitto` — MQTT broker
<<<<<<< HEAD

- `sensor-simulator` — publishes CSV sensor readings

- `control-logic` — processes sensor readings and applies PostgreSQL control settings

- `actuator-simulator` — receives and simulates actuator commands

### MQTT Topics
| Topic | Purpose |

|---|---|

| `sensors/telemetry` | Sensor readings published by the Sensor Simulator |

=======
- `sensor-simulator` — publishes CSV sensor readings
- `control-logic` — processes sensor readings and applies PostgreSQL control settings
- `actuator-simulator` — receives and simulates actuator commands

### MQTT Topics

| Topic | Purpose |
|---|---|
| `sensors/telemetry` | Sensor readings published by the Sensor Simulator |
>>>>>>> main
| `actuators/commands` | Commands published by Control Logic |

All three Python services connect to the Docker MQTT broker using `mosquitto:1883`.

### Starting the Containers
<<<<<<< HEAD
Open PowerShell in the project root directory.

Ensure Docker Desktop is running and the required local PostgreSQL databases are accessible.

Create a local `.env` file containing the required database password:

```dotenv

DB_PASSWORD=your_local_postgresql_password

```

Do not commit `.env` files or database passwords to Git.
=======

Open PowerShell in the project root directory.

Ensure Docker Desktop is running. The telemetry PostgreSQL database runs
from this Compose file; Control Logic's `control_settings_db` is a separate
existing database and must be available using the configured settings.

Create `Prototype/.env` containing the database settings used by the
PostgreSQL container and Python API:

```dotenv
DB_HOST=localhost
DB_PORT=5434
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=choose_a_private_password
```

Do not commit `.env` files or database passwords to Git. Set any Grafana or
Control Logic-specific variables needed by your local setup in this file as
well. Use `--env-file Prototype/.env` with Compose commands so all services
receive the same values.
>>>>>>> main

Build and start the four IoT services:

```powershell
<<<<<<< HEAD

docker compose up -d --build mosquitto control-logic actuator-simulator

=======
docker compose --env-file Prototype/.env up -d --build mosquitto control-logic actuator-simulator
>>>>>>> main
```

Start or replay the Sensor Simulator:

```powershell
<<<<<<< HEAD

docker compose up -d --force-recreate sensor-simulator

=======
docker compose --env-file Prototype/.env up -d --force-recreate sensor-simulator
>>>>>>> main
```

Check container status:

```powershell
<<<<<<< HEAD

docker compose ps

```

### PostgreSQL Configuration
Control Logic currently connects to PostgreSQL running on the host machine.
=======
docker compose --env-file Prototype/.env ps
```

### PostgreSQL Configuration

The telemetry API and Kafka consumer connect to the Compose PostgreSQL
service through `localhost:5434` from Windows. The Dockerized Control Logic
connects to the telemetry service by the Compose hostname `postgres` on port
5432. Its control settings database remains separately configurable.
>>>>>>> main

The Docker Compose configuration uses:

| Variable | Current value |
<<<<<<< HEAD

|---|---|

| `DB_HOST` | `host.docker.internal` |

| `DB_PORT` | `5434` |

| `DB_NAME` | `postgres` by default |

| `CONTROL_DB_HOST` | `host.docker.internal` |

| `CONTROL_DB_PORT` | `5434` |

| `CONTROL_DB_NAME` | `control_settings_db` by default |

The actual database names and credentials must match the local PostgreSQL setup.
=======
|---|---|
| `DB_HOST` | `postgres` inside Docker; `localhost` on Windows |
| `DB_PORT` | `5432` inside Docker; `5434` on Windows |
| `DB_NAME` | `postgres` by default |
| `CONTROL_DB_HOST` | `host.docker.internal` |
| `CONTROL_DB_PORT` | Configured host PostgreSQL port |
| `CONTROL_DB_NAME` | `control_settings_db` by default |

The actual control database name and credentials must match the PostgreSQL
instance containing `control_settings_db`.
>>>>>>> main

Control settings are retrieved from the `control_settings` table, including:

- `temperature_threshold`
<<<<<<< HEAD

- `humidity_threshold`

=======
- `humidity_threshold`
>>>>>>> main
- `light_enabled`

The Control Logic uses these saved values to determine which actuator commands to publish.

<<<<<<< HEAD
**Group integration note:** When Simon's PostgreSQL container is integrated, the database hostnames, ports and service dependencies will need to be updated and retested.

### Testing the Sensor-to-Actuator Flow
Check that the Sensor Simulator publishes CSV readings:

```powershell

docker compose logs --tail=50 sensor-simulator

=======
### Testing the Sensor-to-Actuator Flow

Check that the Sensor Simulator publishes CSV readings:

```powershell
docker compose --env-file Prototype/.env logs --tail=50 sensor-simulator
>>>>>>> main
```

Check that Control Logic receives sensor readings and publishes commands:

```powershell
<<<<<<< HEAD

docker compose logs --tail=100 control-logic

=======
docker compose --env-file Prototype/.env logs --tail=100 control-logic
>>>>>>> main
```

Check that the Actuator Simulator receives commands:

```powershell
<<<<<<< HEAD

docker compose logs --tail=50 actuator-simulator

=======
docker compose --env-file Prototype/.env logs --tail=50 actuator-simulator
>>>>>>> main
```

The expected flow is:

```text
<<<<<<< HEAD

Data_Sensor.py

    |

    v

Mosquitto MQTT (sensors/telemetry)

    |

    v

Control_Logic.py

    |

    +-- PostgreSQL control settings

    |

    v

Mosquitto MQTT (actuators/commands)

    |

    v

Actuator_Simulator.py

```

### Testing Completed
The following tests were completed during SCRUM-102:

- All four IoT components started successfully using Docker Compose.

- The Sensor Simulator published 10 readings from the IoT CSV dataset.

- Control Logic received live MQTT sensor messages.

- Control Logic successfully retrieved PostgreSQL settings.

- Readings exceeding the configured humidity threshold generated Dehumidifier ON commands.

- The Actuator Simulator received and simulated the commands.

- A separate below-threshold test generated no actuator commands.

### Group Handover Notes
=======
Data_Sensor.py
    |
    v
Mosquitto MQTT (sensors/telemetry)
    |
    v
Control_Logic.py
    |
    +-- PostgreSQL control settings
    |
    v
Mosquitto MQTT (actuators/commands)
    |
    v
Actuator_Simulator.py
```

### Testing Completed

The following tests were completed during SCRUM-102:

- All four IoT components started successfully using Docker Compose.
- The Sensor Simulator published 10 readings from the IoT CSV dataset.
- Control Logic received live MQTT sensor messages.
- Control Logic successfully retrieved PostgreSQL settings.
- Readings exceeding the configured humidity threshold generated Dehumidifier ON commands.
- The Actuator Simulator received and simulated the commands.
- A separate below-threshold test generated no actuator commands.

### Group Handover Notes

>>>>>>> main
The IoT control components have been containerised and tested together.

Before the full group deployment, the following integration points should be reviewed:

<<<<<<< HEAD
1. Replace the current host-based PostgreSQL connections when the database container is available.

2. Verify that Kafka Connect uses the Docker Mosquitto broker instead of the old Windows broker.

3. Remove or replace the Windows-specific Kafka Connect plugin path for deployment on other machines.

4. Confirm that all services start correctly using the group's final Docker Compose configuration.

5. Retest the complete sensor, Kafka, database, control and actuator flow after the group components are integrated.

### Stopping the Services
Stop the IoT components without removing the rest of the group's running services:

```powershell

docker compose stop sensor-simulator control-logic actuator-simulator mosquitto

=======
1. Confirm that the existing `control_settings_db` is reachable using the
   configured `CONTROL_DB_*` settings.
2. Verify that Kafka Connect loads the MQTT plugin from the configured host
   plugin directory.
3. Replace the Windows-specific Kafka Connect plugin path when running on a
   different operating system.
4. Confirm that all services start correctly using the local
   `Prototype/.env`.
5. Retest the complete sensor, Kafka, telemetry database, control and
   actuator flow after starting the merged Compose stack.

### Stopping the Services

Stop the IoT components without removing the rest of the group's running services:

```powershell
docker compose --env-file Prototype/.env stop sensor-simulator control-logic actuator-simulator mosquitto
>>>>>>> main
```

The MQTT broker currently allows anonymous connections for local development. Authentication and appropriate access controls should be added before production deployment.

## Control API
<<<<<<< HEAD
The Control API runs as a Docker Compose service alongside the other project components. It provides API endpoints for accessing and managing the control system.

### Prerequisites
- Docker Desktop is installed and running.

- The project repository has been cloned.

=======

The Control API runs as a Docker Compose service alongside the other project components. It provides API endpoints for accessing and managing the control system.

### Prerequisites

- Docker Desktop is installed and running.
- The project repository has been cloned.
>>>>>>> main
- The required environment variables and database settings are configured in the project's local `.env` file.

Do not commit passwords or other secrets to Git.

### Start the Control API
<<<<<<< HEAD
Run these commands from the project root:

```powershell

docker compose config --quiet

docker compose up -d --build control-api

=======

Run these commands from the project root:

```powershell
docker compose --env-file Prototype/.env config --quiet
docker compose --env-file Prototype/.env up -d --build control-api
>>>>>>> main
```

Check the service status:

```powershell
<<<<<<< HEAD

docker compose ps control-api

=======
docker compose --env-file Prototype/.env ps control-api
>>>>>>> main
```

View the API logs if needed:

```powershell
<<<<<<< HEAD

docker compose logs --tail=50 control-api

```

### Access the API
=======
docker compose --env-file Prototype/.env logs --tail=50 control-api
```

### Access the API

>>>>>>> main
Once the service is running, open the interactive API documentation:

`http://localhost:8000/docs`

### Stop the Control API
<<<<<<< HEAD
To stop only the Control API:

```powershell

docker compose stop control-api

=======

To stop only the Control API:

```powershell
docker compose --env-file Prototype/.env stop control-api
>>>>>>> main
```

To rebuild and restart it after code changes:

```powershell
<<<<<<< HEAD

docker compose up -d --build control-api

```

### Troubleshooting
- If the container does not start, check the logs using `docker compose logs control-api`.

- If port 8000 is already in use, check for another service using that port.

- If the API cannot connect to the database, check the `.env` settings and confirm that the database service or configured database host is reachable.

- If the Compose configuration is invalid, run `docker compose config` to display the resolved configuration and look for errors.

---

## 7. User Authentication API (SCRUM-140)
The API includes user registration and login functionality using FastAPI, PostgreSQL, Argon2id password hashing and JSON Web Tokens (JWT).

Authentication uses a separate PostgreSQL database connection from the telemetry and control-settings connections.

### 7.1 Authentication endpoints
| Method | Path | Purpose | Expected response |

|---|---|---|---|

| POST | `/auth/register` | Register a new user | 201 Created |

| POST | `/auth/login` | Authenticate an existing user | 200 OK |

| GET | `/auth/me` | Retrieve the currently authenticated user's details | 200 OK |

The `/auth/me` endpoint requires a valid Bearer token in the Authorization header.

### 7.2 Authentication database
The authentication schema is located at:

`Prototype/docs/scrum108_schema.sql`

It creates the following tables:

- `users` – registered user details and password hashes.

- `buildings` – building records.

- `building_members` – user membership and role information.

- `building_devices` – devices associated with buildings.

It also adds a `building_id` relationship and index to the existing `control_settings` table.

The schema expects the `control_settings` table to exist before it is executed.

### 7.3 Authentication environment variables
Add the following settings to your local `Prototype/.env` file:

```dotenv

AUTH_DB_HOST=localhost

AUTH_DB_PORT=5436

AUTH_DB_NAME=scrum108_test_db

AUTH_DB_USER=postgres

AUTH_DB_PASSWORD=\<your_auth_database_password>

AUTH_SECRET_KEY=\<your_private_random_secret>

```

Use your own database credentials and generate a strong random JWT signing secret. Do not commit `.env` files or share secret values.

The port and database name above represent the local development configuration. Developers can use different values for their own PostgreSQL installations.

### 7.4 Create the authentication database
Create a PostgreSQL database for authentication, then execute the schema against it.

For example, using `psql`:

```powershell

createdb -U postgres -h localhost -p 5436 scrum108_test_db

```

The database must also have the existing `control_settings` table before applying the complete schema.

From the `Prototype` directory, apply the schema:

```powershell

psql -U postgres -h localhost -p 5436 -d scrum108_test_db -f docs/scrum108_schema.sql

```

If the database or required table already exists, check the existing setup before running the schema.

### 7.5 Password security and JWT authentication
- Passwords are hashed using Argon2id before being stored.

- Plain-text passwords are not stored in the users table.

- Successful login returns a JWT access token.

- Tokens use HS256 signing and expire after 30 minutes.

- Protected requests must include:

```http

Authorization: Bearer \<your_access_token>

```

### 7.6 Testing authentication
Use Swagger UI:

`http://127.0.0.1:8000/docs`

Test the endpoints in this order:

1. Register a user using `POST /auth/register`.

2. Log in using `POST /auth/login`.

3. Copy the returned access token.

4. Select **Authorize** in Swagger and enter the Bearer token.

5. Call `GET /auth/me` to retrieve the authenticated user's profile.

Expected error responses include:

- `401` – incorrect login credentials, missing token or invalid/expired token.

- `409` – email address already registered.

- `422` – request validation failed.

---

# SCRUM-108 — Multi-Building Database Design and Migration Notes

*Historical design and isolated-test evidence. This is not proof of deployment to the team's shared ControlDB.*

The design extends `control_settings_db` while leaving the telemetry database separate. The original proposed entities were:

| Table | Fields and purpose |
|---|---|
| `users` | `user_id` primary key, `full_name`, unique `email`, `password_hash`, `created_at` |
| `buildings` | `building_id` primary key, `building_name`, unique `building_code`, `created_by`, `created_at` |
| `building_members` | `membership_id` primary key, `user_id`, `building_id`, `role` (`admin`/`member`), `status` (`pending`/`approved`/`rejected`), `joined_at` |
| `control_settings` | Existing control settings extended with a building-specific `building_id` foreign key |
| `building_devices` | Proposed mapping between device identifiers and building IDs |

A user can belong to several buildings; each building can have several users. The building creator should automatically be its admin. A user can request membership using the building code; an administrator approves or rejects the request. Only approved members should access a building's data. These are design requirements and must be enforced in the API, not assumed from the database tables alone.

## Original implementation investigation

At the time of SCRUM-108, `GET /control-settings` and `PUT /control-settings` used the global `control_settings` record `WHERE id = 1`. `Control_Logic.py` also retrieved settings with `get_control_settings()` against `id = 1`, so the automated controls shared a single threshold set. The control model contained `temperature_threshold`, `humidity_threshold`, `light_enabled` and `updated_at`. The telemetry API exposed GET, POST, PUT and DELETE operations with fields `records`, `ts`, `device`, `co`, `humidity`, `light`, `lpg`, `motion`, `smoke` and `temp`, but had no `building_id`. The `device` field was the available identifier for building-to-sensor mapping.

## Isolated schema test and migration safety

The proposed schema was created and tested in a separate PostgreSQL Docker test database. The tests covered users, buildings, membership relationships, per-building settings and database constraints. The original global settings row was preserved with `building_id = NULL`, while Building A and Building B received separate records. At the time of the SCRUM-108 report, **the team's shared ControlDB and telemetry database had not been modified**.

The SQL migration source remains at `Prototype/docs/scrum108_schema.sql` (a SQL file, not an extra Markdown document). It depends on the existing `control_settings` table, so initialise that table before running the migration. Before applying to shared infrastructure: back up the database; preserve existing telemetry and initialisation; review primary/foreign keys and unique constraints; store only hashed passwords; verify membership and building-scoped API access; map sensors to buildings; and test the new control logic before retiring global `id = 1` behaviour. The later authentication documentation above describes a separate subsequent implementation and does not retroactively change the SCRUM-108 test status.

# SCRUM-122 — Multi-Building Control Isolation Test Evidence

**Test date:** 2 November 2026. **Branch:** `liam/multi-building-control`. **Code under test:** `Prototype/Control_Logic.py`. **Method:** in-process Python tests using mocked PostgreSQL connections, MQTT clients and building mappings. These were *mocked isolation tests*, not a live end-to-end deployment test.

Both simulated buildings received the same input (`temp = 28`, `humidity = 75`, `light = true`) but had different settings:

| Setting | House 1 | House 2 |
|---|---|---|
| `building_id` | 1 | 2 |
| Temperature threshold | 25 C | 30 C |
| Humidity threshold | 70% | 80% |
| Light enabled | `true` | `false` |
| Expected commands | Fan ON, Dehumidifier ON, Light ON | None |

| Test | Expected and observed outcome | Result |
|---|---|---|
| Control decision isolation | House 1 generated all three commands; House 2 generated none | PASS |
| MQTT command isolation | Building-specific topics and `building_id` in JSON payloads verified with mocked MQTT client | PASS |
| Sensor-to-actuator flow | House 1 produced three commands on its topic, House 2 none, with mocked mappings/settings | PASS |
| Database settings retrieval | SQL settings queries used `building_id = 1` and `building_id = 2` and returned distinct mocked thresholds | PASS |

The building-specific command topics verified were `buildings/1/actuators/commands` and `buildings/2/actuators/commands`. Evidence screenshot names recorded for Jira:

- `SCRUM-122-Control-Isolation.png`
- `SCRUM-122-MQTT-Isolation.png`
- `SCRUM-122-End-to-End-Isolation.png`
- `SCRUM-122-Database-Isolation.png`

**Limitations and outstanding work:** Database settings and connections were mocked; MQTT publishing was not tested with a live broker; device-building mappings were mocked. Live persistence, cross-building update isolation and complete frontend/authentication/PostgreSQL/MQTT end-to-end behaviour remained unverified. The original report noted that SCRUM-121 disabled the legacy control-settings endpoints and that the frontend required migration. The team still needed to agree the admin-only update policy. Thus the four PASS results establish **logic isolation under mocks only**, not production-ready multi-building isolation.
=======
docker compose --env-file Prototype/.env up -d --build control-api
```

### Troubleshooting

- If the container does not start, check the logs using `docker compose --env-file Prototype/.env logs control-api`.
- If port 8000 is already in use, check for another service using that port.
- If the API cannot connect to the database, check the `.env` settings and confirm that the database service or configured database host is reachable.
- If the Compose configuration is invalid, run `docker compose --env-file Prototype/.env config` to display the resolved configuration and look for errors.
>>>>>>> main
