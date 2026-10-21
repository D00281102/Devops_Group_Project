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