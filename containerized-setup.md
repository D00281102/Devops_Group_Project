# Containerized Kafka Setup

This guide runs Kafka, Kafka UI, and Kafka Connect with Docker Compose. Mosquitto and the Python sensor run outside Docker on Windows. The Kafka consumer is started by the Kafka automation script.

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
    +--> Kafka consumer on Windows
```

## Prerequisites

Install and start:

- Docker Desktop
- Python 3
- Eclipse Mosquitto
- Apache Kafka tools and Kafka Connect

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

The startup script starts Kafka, Kafka UI, Kafka Connect, the Kafka topic, the MQTT connector, and the Kafka consumer.

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

## Start Mosquitto and the MQTT Subscriber

Start Mosquitto in its own terminal:

```powershell
& "C:\Program Files\mosquitto\mosquitto.exe" -v
```

In another terminal, subscribe to the sensor topic:

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

## Current Scope

The current Compose file containerizes Kafka and Kafka UI only. A fully containerized setup would also need Compose services for Mosquitto, Kafka Connect, the MQTT connector plugin, the sensor, and the Kafka consumer.
