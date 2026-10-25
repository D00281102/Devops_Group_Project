# Containerised IoT and Kafka Setup

This guide covers the project's Docker Compose setup, including Kafka, Kafka Connect, Kafka UI, Mosquitto MQTT, the Sensor Simulator, Control Logic, Actuator Simulator and Grafana.

**Note:** The original Kafka setup instructions below describe the earlier Windows-based configuration, where Mosquitto and the Sensor Simulator ran outside Docker. These instructions are retained for reference and may not match the current Compose configuration.

For the current containerised Sensor Simulator, Control Logic, Actuator Simulator and Mosquitto setup, see **Dockerised IoT Control System — SCRUM-102** further down this document.

For the original manual Windows setup, see [local-setup.md](local-setup.md).

## Architecture

```text
Data_Sensor.py
    |
    | MQTT: localhost:1883
    v
Mosquitto on Windows
    |
    | MQTT source connector
    v
Kafka Connect in Docker
    |
    | Kafka: localhost:9092
    v
Kafka in Docker
    |
    +--> Kafka UI in Docker: http://localhost:8080
    |
    +--> Kafka consumer on Windows
```

## Prerequisites

Install and start:

- Docker Desktop
- Python 3
- Eclipse Mosquitto installed at `C:\Program Files\mosquitto`
- Apache Kafka tools installed at `C:\kafka`

Mosquitto does not need to be started manually. The project startup script starts it automatically using the configuration file at:

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

## Network Addresses

Windows applications use the ports:

```text
Kafka: localhost:9092
MQTT: localhost:1883
Kafka Connect REST API: localhost:8083
Kafka UI: http://localhost:8080
```

Docker containers use these internal addresses:

```text
Kafka: kafka:9093

MQTT from Kafka Connect: host.docker.internal:1883
```

Kafka UI is configured to use `kafka:9093` in `docker-compose.yml`.

## Start the Kafka Services Automatically

From the project root:

The startup script automatically starts Mosquitto, Kafka, Kafka UI, Kafka Connect, the Kafka topic, the MQTT connector, and the Kafka consumer. Mosquitto uses the project's `Prototype/mosquitto.conf` configuration so that Kafka Connect running in Docker can connect to the MQTT broker.

Run it from the project root:

```powershell
Set-Location "C:\Devops_Group_Project" (This is to set your directory)
py .\Prototype\scripts\start_kafka.py
```

Check the containers:

```powershell
docker compose ps
```

Follow Kafka logs if needed:

```powershell
docker compose logs -f kafka
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
http://localhost:8080
```

The script waits for Kafka before creating `sensor-telemetry`. It also waits for Kafka Connect before registering the MQTT source connector.

Check the running services:

```powershell
docker compose ps
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

The sensor currently uses `localhost:1883`, which is correct because Mosquitto is running on Windows.

## View Data in Kafka UI

1. Open `http://localhost:8080`.
2. Select the `local` cluster.
3. Open the `sensor-telemetry` topic.
4. Select the `Messages` tab.
5. Set the value format to `String` or `UTF-8`.
6. Refresh the messages.

The topic should contain the JSON sensor records.

## Stop the Setup

Stop the Windows processes with `Ctrl+C`, then stop Docker services:

```powershell
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to remove Docker volumes and stored Kafka data.

## Previous Setup Scope (Historical)

The current Compose file containerizes Kafka and Kafka UI only. A fully containerized setup would also need Compose services for Mosquitto, Kafka Connect, the MQTT connector plugin, the sensor, and the Kafka consumer.

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

Ensure Docker Desktop is running and the required local PostgreSQL databases are accessible.

Create a local `.env` file containing the required database password:

```dotenv
DB_PASSWORD=your_local_postgresql_password
```

Do not commit `.env` files or database passwords to Git.

Build and start the four IoT services:

```powershell
docker compose up -d --build mosquitto control-logic actuator-simulator
```

Start or replay the Sensor Simulator:

```powershell
docker compose up -d --force-recreate sensor-simulator
```

Check container status:

```powershell
docker compose ps
```

### PostgreSQL Configuration

Control Logic currently connects to PostgreSQL running on the host machine.

The Docker Compose configuration uses:

| Variable | Current value |
|---|---|
| `DB_HOST` | `host.docker.internal` |
| `DB_PORT` | `5434` |
| `DB_NAME` | `postgres` by default |
| `CONTROL_DB_HOST` | `host.docker.internal` |
| `CONTROL_DB_PORT` | `5434` |
| `CONTROL_DB_NAME` | `control_settings_db` by default |

The actual database names and credentials must match the local PostgreSQL setup.

Control settings are retrieved from the `control_settings` table, including:

- `temperature_threshold`
- `humidity_threshold`
- `light_enabled`

The Control Logic uses these saved values to determine which actuator commands to publish.

**Group integration note:** When Simon's PostgreSQL container is integrated, the database hostnames, ports and service dependencies will need to be updated and retested.

### Testing the Sensor-to-Actuator Flow

Check that the Sensor Simulator publishes CSV readings:

```powershell
docker compose logs --tail=50 sensor-simulator
```

Check that Control Logic receives sensor readings and publishes commands:

```powershell
docker compose logs --tail=100 control-logic
```

Check that the Actuator Simulator receives commands:

```powershell
docker compose logs --tail=50 actuator-simulator
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

1. Replace the current host-based PostgreSQL connections when the database container is available.
2. Verify that Kafka Connect uses the Docker Mosquitto broker instead of the old Windows broker.
3. Remove or replace the Windows-specific Kafka Connect plugin path for deployment on other machines.
4. Confirm that all services start correctly using the group's final Docker Compose configuration.
5. Retest the complete sensor, Kafka, database, control and actuator flow after the group components are integrated.

### Stopping the Services

Stop the IoT components without removing the rest of the group's running services:

```powershell
docker compose stop sensor-simulator control-logic actuator-simulator mosquitto
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
docker compose config --quiet
docker compose up -d --build control-api
```

Check the service status:

```powershell
docker compose ps control-api
```

View the API logs if needed:

```powershell
docker compose logs --tail=50 control-api
```

### Access the API

Once the service is running, open the interactive API documentation:

`http://localhost:8000/docs`

### Stop the Control API

To stop only the Control API:

```powershell
docker compose stop control-api
```

To rebuild and restart it after code changes:

```powershell
docker compose up -d --build control-api
```

### Troubleshooting

- If the container does not start, check the logs using `docker compose logs control-api`.
- If port 8000 is already in use, check for another service using that port.
- If the API cannot connect to the database, check the `.env` settings and confirm that the database service or configured database host is reachable.
- If the Compose configuration is invalid, run `docker compose config` to display the resolved configuration and look for errors.



## ControlDB Containerization — SCRUM-104

### Overview

The Control Settings Database (ControlDB) stores user-configurable temperature, humidity and light settings.

The Control API saves settings to ControlDB, and the Control Logic reads those settings to make actuator decisions.

ControlDB is separate from the telemetry database used for sensor data.

### Database Configuration

- Docker service: `control-db`
- Database: `control_settings_db`
- Table: `control_settings`
- PostgreSQL version: 17
- Docker image: `ghcr.io/baosystems/postgis:17-3.5`
- Windows connection: `localhost:5435`
- Docker connection: `control-db:5432`
- Persistent volume: `controldb-data`

The PostGIS image is currently used because the official PostgreSQL image could not be downloaded during local testing.

### Environment Setup

Create a `.env` file in the project root using `.env.example` as a template.

Set the following variable:

```dotenv
CONTROL_DB_PASSWORD=your_local_control_db_password
```

Do not commit `.env` or actual database passwords to GitHub.

### Start ControlDB

The persistent volume is currently configured as an external Docker volume.

Create it before starting ControlDB for the first time:

```powershell
docker volume create controldb-data
```

Validate the Docker Compose configuration:

```powershell
docker compose config --quiet
```

Start ControlDB:

```powershell
docker compose up -d control-db
```

Check that the container is healthy:

```powershell
docker compose ps control-db
```

### Automatic Database Initialization

The file `Prototype/control_settings_docker.sql` is mounted into `/docker-entrypoint-initdb.d/`.

When PostgreSQL initializes an empty data directory, the script automatically creates the `control_settings` table and inserts the default settings:

- Temperature threshold: 25
- Humidity threshold: 70
- Light enabled: true

The script does not overwrite existing settings when rerun.

### Verify the Database

Run:

```powershell
docker compose exec control-db psql -U postgres -d control_settings_db -c "SELECT id, temperature_threshold, humidity_threshold, light_enabled FROM control_settings;"
```

This displays the saved settings.

### Data Persistence

ControlDB stores its PostgreSQL data in the named Docker volume `controldb-data`.

The database was tested successfully after:

- Restarting the container.
- Recreating the container.
- Updating the temperature threshold from 25 to 28.

The updated setting remained saved after both tests.

Do not use `docker compose down -v` or delete the `controldb-data` volume unless you intentionally want to remove stored database data.

### Integration

The Control API and Control Logic use these Docker network connection details:

```dotenv
CONTROL_DB_HOST=control-db
CONTROL_DB_PORT=5432
CONTROL_DB_NAME=control_settings_db
CONTROL_DB_USER=postgres
```

The ControlDB password is supplied separately through `CONTROL_DB_PASSWORD`.

The telemetry database remains separate and uses its own connection settings.

Full end-to-end integration should be retested after all group services are running together.

### Stop ControlDB

```powershell
docker compose stop control-db
```

This stops PostgreSQL without deleting its persistent volume.
