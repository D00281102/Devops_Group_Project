# Containerised IoT and Kafka Setup

This guide covers the project's Docker Compose setup, including PostgreSQL
with a persistent data volume, Kafka, Kafka Connect, Kafka UI, Mosquitto,
the Sensor Simulator, Control Logic, Actuator Simulator, the Control API,
and Grafana. The Windows-hosted Kafka consumer can also write telemetry to
the PostgreSQL container through the published host port.

**Note:** The Kafka section below includes the earlier Windows-based Kafka
Connect plugin setup. The current Compose stack runs Mosquitto and the
Sensor Simulator in Docker; Kafka Connect loads its MQTT plugin from the
configured host plugin directory.

For the current containerised Sensor Simulator, Control Logic, Actuator Simulator and Mosquitto setup, see **Dockerised IoT Control System — SCRUM-102** further down this document.

For the original manual Windows setup, see [local-setup.md](local-setup.md).

## Architecture
```text
Sensor Simulator (Docker) or Data_Sensor.py (Windows)
    |
    | MQTT: mosquitto:1883 (Docker) or localhost:1883 (Windows)
    v
Mosquitto in Docker
    |
    | MQTT source connector via host.docker.internal:1883
    v
Kafka Connect in Docker

    |

    | Kafka: localhost:9092

    v

Kafka in Docker
    |
    +--> Kafka UI in Docker: http://localhost:8081
    |
    +--> Database consumer on Windows
              |
              v
        PostgreSQL in Docker
        (`iot_telemetry_data`, persistent volume)
```

## Prerequisites
Install and start:

- Docker Desktop

- Python 3
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

## PostgreSQL databases and initialization

Compose runs one PostgreSQL server with persistent storage in the
`postgres_data` volume. It initializes the telemetry database (the `DB_NAME`,
`postgres` by default) and a separate `control_settings_db`. Authentication
and control tables share `control_settings_db`, matching the combined
SCRUM-111 schema and the application's building/device relationships.

The `database-init` service creates the control database if needed, then
idempotently initializes the telemetry table, default control settings, and
authentication/building tables. The API and Control Logic wait for that
service to complete before starting. The initializer can also run against an
existing PostgreSQL volume without deleting its data.

Create `Prototype/.env` from `.env.example`, set `DB_PASSWORD` and
`AUTH_SECRET_KEY` to private values, and set `CONTROL_DB_PASSWORD` and
`AUTH_DB_PASSWORD` to the same PostgreSQL password. Start the stack from the
repository root:

```powershell
docker compose --env-file Prototype/.env up -d
```

Windows-hosted applications connect at `localhost:5434`; Compose services
connect to `postgres:5432`. Do not run `docker compose down -v` unless you
intend to delete the persistent PostgreSQL data.

Confirm both databases and their tables were initialized:

```powershell
docker compose --env-file Prototype/.env exec postgres psql -U postgres -d postgres -c "\dt"
docker compose --env-file Prototype/.env exec postgres psql -U postgres -d control_settings_db -c "\dt"
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

For an empty Docker volume, wait until the telemetry backup has been restored
before starting `database-init`; the initializer creates the telemetry table.

Wait for `docker compose --env-file Prototype/.env ps postgres` to show the
container as healthy.

Restore the backup into the container:

```powershell
psql -h localhost -p 5434 -U postgres -d postgres -v ON_ERROR_STOP=1 -f .\Prototype\data\telemetry-backup.sql
```

Then initialize the remaining tables and the control/authentication database:

```powershell
docker compose --env-file Prototype/.env run --rm database-init
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
Kafka UI: http://localhost:8081
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
Set-Location "C:\Devops_Group_Project"
py .\Prototype\scripts\start_kafka.py

```

Leave this terminal running; it remains attached to the database consumer.
Start the sensor in another terminal using the command in **Start the Sensor**.

Check the containers:

```powershell
docker compose --env-file Prototype/.env ps
```

Follow Kafka logs if needed:

```powershell
docker compose --env-file Prototype/.env logs -f kafka
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
http://localhost:8081
```

The script waits for Kafka before creating `sensor-telemetry`. It also waits for Kafka Connect before registering the MQTT source connector.

Check the running services:

```powershell
docker compose --env-file Prototype/.env ps
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

1. Open `http://localhost:8081`.
2. Select the `local` cluster.

3. Open the `sensor-telemetry` topic.

4. Select the `Messages` tab.

5. Set the value format to `String` or `UTF-8`.

6. Refresh the messages.

The topic should contain the JSON sensor records.

## Stop the Setup
Stop the Windows processes with `Ctrl+C`, then stop Docker services:

```powershell
docker compose --env-file Prototype/.env down
```

This stops containers but preserves the PostgreSQL volume and its data. Do
not use `docker compose --env-file Prototype/.env down -v` unless you
intentionally want to delete the database volume and stored Kafka data.

## Previous Setup Scope (Historical)

The current Compose file runs PostgreSQL, Kafka, Kafka UI, Kafka Connect,
Mosquitto, Grafana, and the IoT control components in Docker. The Windows
Kafka consumer remains a separate process and connects to PostgreSQL using
`Prototype/.env`.

## Dockerised IoT Control System — 21/10/26 updated

### Overview

The IoT control components have been containerised using Docker Compose. The system reads sensor data from a CSV file, publishes readings through MQTT, evaluates configurable control rules and sends commands to an actuator simulator.

The relevant services are:

- `mosquitto` — MQTT broker
- `sensor-simulator` — publishes CSV sensor readings
- `control-logic` — processes sensor readings and applies PostgreSQL control settings
- `actuator-simulator` — receives and simulates actuator commands

### MQTT Topics

| Topic | Purpose |
|---|---|
| `sensors/telemetry` | Sensor readings published by the Sensor Simulator |
| `actuators/commands` | Commands published by Control Logic |

All three Python services connect to the Docker MQTT broker using `mosquitto:1883`.

### Starting the Containers

Open PowerShell in the project root directory.

Ensure Docker Desktop is running. Compose initializes the telemetry database
and the combined control/authentication `control_settings_db` on the same
PostgreSQL server.

Create `Prototype/.env` from the repository's `.env.example`. Set private
values for `DB_PASSWORD` and `AUTH_SECRET_KEY`. The control and authentication
database names should both be `control_settings_db`, with the same PostgreSQL
user and password:

```dotenv
DB_HOST=localhost
DB_PORT=5434
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=choose_a_private_password
CONTROL_DB_HOST=localhost
CONTROL_DB_PORT=5434
CONTROL_DB_NAME=control_settings_db
CONTROL_DB_USER=postgres
CONTROL_DB_PASSWORD=choose_a_private_password
AUTH_DB_HOST=localhost
AUTH_DB_PORT=5434
AUTH_DB_NAME=control_settings_db
AUTH_DB_USER=postgres
AUTH_DB_PASSWORD=choose_a_private_password
AUTH_SECRET_KEY=replace_with_a_secure_random_secret
```

Do not commit `.env` files or database passwords to Git. Set any Grafana or
Control Logic-specific variables needed by your local setup in this file as
well. Use `--env-file Prototype/.env` with Compose commands so all services
receive the same values.

Build and start the four IoT services:

```powershell
docker compose --env-file Prototype/.env up -d --build mosquitto control-logic actuator-simulator
```

Start or replay the Sensor Simulator:

```powershell
docker compose --env-file Prototype/.env up -d --force-recreate sensor-simulator
```

Check container status:

```powershell
docker compose --env-file Prototype/.env ps
```

### PostgreSQL Configuration

The telemetry API and Kafka consumer connect to the Compose PostgreSQL
service through `localhost:5434` from Windows. The Dockerized Control Logic
connects to the PostgreSQL server by the Compose hostname `postgres` on port
5432. Its control/authentication database is `control_settings_db`.

The Docker Compose configuration uses:

| Variable | Current value |
|---|---|
| `DB_HOST` | `postgres` inside Docker; `localhost` on Windows |
| `DB_PORT` | `5432` inside Docker; `5434` on Windows |
| `DB_NAME` | `postgres` by default |
| `CONTROL_DB_HOST` | `postgres` inside Docker; `localhost` on Windows |
| `CONTROL_DB_PORT` | `5432` inside Docker; `5434` on Windows |
| `CONTROL_DB_NAME` | `control_settings_db` by default |
| `AUTH_DB_NAME` | Same as `CONTROL_DB_NAME` |

`database-init` creates and initializes `control_settings_db` on the Compose
PostgreSQL server. The Compose API and Control Logic services use the internal
Docker hostname; local Windows processes use the published host port.

Control settings are retrieved from the `control_settings` table, including:

- `temperature_threshold`
- `humidity_threshold`
- `light_enabled`

The Control Logic uses these saved values to determine which actuator commands to publish.

### Testing the Sensor-to-Actuator Flow

Check that the Sensor Simulator publishes CSV readings:

```powershell
docker compose --env-file Prototype/.env logs --tail=50 sensor-simulator
```

Check that Control Logic receives sensor readings and publishes commands:

```powershell
docker compose --env-file Prototype/.env logs --tail=100 control-logic
```

Check that the Actuator Simulator receives commands:

```powershell
docker compose --env-file Prototype/.env logs --tail=50 actuator-simulator
```

The expected flow is:

```text
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

The IoT control components have been containerised and tested together.

Before the full group deployment, the following integration points should be reviewed:

1. Confirm that `database-init` completes successfully and both applications
   connect to the initialized `control_settings_db`.
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
```

The MQTT broker currently allows anonymous connections for local development. Authentication and appropriate access controls should be added before production deployment.

## Control API

The Control API runs as a Docker Compose service alongside the other project components. It provides API endpoints for accessing and managing the control system.

### Prerequisites

- Docker Desktop is installed and running.
- The project repository has been cloned.
- The required environment variables and database settings are configured in the project's local `.env` file.

Do not commit passwords or other secrets to Git.

### Start the Control API

Run these commands from the project root:

```powershell
docker compose --env-file Prototype/.env config --quiet
docker compose --env-file Prototype/.env up -d --build control-api
```

Check the service status:

```powershell
docker compose --env-file Prototype/.env ps control-api
```

View the API logs if needed:

```powershell
docker compose --env-file Prototype/.env logs --tail=50 control-api
```

### Access the API

Once the service is running, open the interactive API documentation:

`http://localhost:8000/docs`

### Stop the Control API

To stop only the Control API:

```powershell
docker compose --env-file Prototype/.env stop control-api
```

To rebuild and restart it after code changes:

```powershell
docker compose --env-file Prototype/.env up -d --build control-api
```

### Troubleshooting

- If the container does not start, check the logs using `docker compose --env-file Prototype/.env logs control-api`.
- If port 8000 is already in use, check for another service using that port.
- If the API cannot connect to the database, check the `.env` settings and confirm that the database service or configured database host is reachable.
- If the Compose configuration is invalid, run `docker compose --env-file Prototype/.env config` to display the resolved configuration and look for errors.
