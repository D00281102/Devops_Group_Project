# Containerized Kafka Setup

This guide runs PostgreSQL, Kafka, Kafka UI, and Kafka Connect with Docker Compose. PostgreSQL uses a persistent named volume. Mosquitto, the Python sensor, and the database consumer run outside Docker on Windows.

For the complete manual Windows setup, see [local-setup.md](local-setup.md).

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

## Move the existing database into Docker

Back up the existing local PostgreSQL database before stopping it. Run from
the repository root while local PostgreSQL is running:

```powershell
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

Wait for `docker compose ps postgres` to show the container as healthy.

Restore the backup into the container:

```powershell
psql -h localhost -p 5434 -U postgres -d postgres -f .\Prototype\data\telemetry-backup.sql
```

The compose service keeps the database in the `postgres_data` named volume.
Restarting or running `docker compose down` preserves the data. Avoid
`docker compose down -v`, which deletes that volume.

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
The Windows API and database consumer connect to PostgreSQL at
`localhost:5434`, as configured in `Prototype/.env`. Other Docker services
can connect to PostgreSQL using `postgres:5432`.

## Start the Kafka Services Automatically

From the project root:

Start PostgreSQL separately using the command in **Move the existing
database into Docker**. The Kafka startup script starts Mosquitto, Kafka,
Kafka UI, Kafka Connect, the Kafka topic, the MQTT connector, and a Python
consumer that writes records into the same PostgreSQL
`iot_telemetry_data` table. The consumer uses the `Prototype/.env` settings
shared with the API. Mosquitto uses the project's `Prototype/mosquitto.conf`
configuration so Kafka Connect running in Docker can connect to the MQTT
broker.

Run it from the project root:

```powershell
Set-Location "C:\Devops_Group_Project" (This is to set your directory)
py .\Prototype\scripts\start_kafka.py
```

Leave this terminal running; it remains attached to the database consumer.
Start the sensor in another terminal using the command in **Start the Sensor**.

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

This stops containers but preserves the PostgreSQL volume and its data. Do
not use `docker compose down -v` unless you intentionally want to delete the
database volume and stored Kafka data.

## Current Scope

PostgreSQL, Kafka, Kafka UI, and Kafka Connect run in Docker. Mosquitto, the sensor, and the database consumer run on Windows.
