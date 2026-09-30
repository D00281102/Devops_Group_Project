# Containerized Kafka Setup

This guide runs Kafka and Kafka UI with Docker Compose. Mosquitto, Kafka Connect, the Kafka consumer, and the Python sensor currently run outside Docker.

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
Kafka Connect on Windows
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

Docker containers use the Kafka service name and internal listener:

```text
Kafka: kafka:9093
```

Kafka UI is configured to use `kafka:9093` in `docker-compose.yml`.

## Start Kafka and Kafka UI

From the project root:

```powershell
docker compose up -d kafka kafka-ui or docker compose up -d
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

## Create the Kafka Topic

Use the Kafka tools from the existing local Kafka installation:

```powershell
Set-Location "C:\kafka"

.\bin\windows\kafka-topics.bat `
  --create `
  --topic sensor-telemetry `
  --bootstrap-server localhost:9092 `
  --partitions 1 `
  --replication-factor 1
```

If the topic already exists, continue to the next step.

Verify it:

```powershell
.\bin\windows\kafka-topics.bat --list --bootstrap-server localhost:9092
```

## Start Kafka Connect

Kafka Connect is not currently defined in `docker-compose.yml`, so start it separately:

```powershell
Set-Location "C:\kafka"
.\bin\windows\connect-distributed.bat .\config\connect-distributed.properties
```

The Connect configuration must use:

```properties
bootstrap.servers=localhost:9092
plugin.path=C:/kafka/plugins
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

## Register the MQTT Connector

Run this in a separate PowerShell terminal:

```powershell
$body = @{
    name = "mqtt-source"
    config = @{
        "connector.class" = "io.confluent.connect.mqtt.MqttSourceConnector"
        "tasks.max" = "1"
        "mqtt.server.uri" = "tcp://localhost:1883"
        "mqtt.topics" = "sensors/telemetry"
        "mqtt.qos" = "0"
        "kafka.topic" = "sensor-telemetry"
        "confluent.topic.bootstrap.servers" = "localhost:9092"
        "confluent.topic.replication.factor" = "1"
        "key.converter" = "org.apache.kafka.connect.storage.StringConverter"
        "value.converter" = "org.apache.kafka.connect.converters.ByteArrayConverter"
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Method Post `
    -Uri "http://localhost:8083/connectors" `
    -ContentType "application/json" `
    -Body $body
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

## Start the Kafka Consumer

```powershell
Set-Location "C:\kafka"

.\bin\windows\kafka-console-consumer.bat `
  --bootstrap-server localhost:9092 `
  --topic sensor-telemetry `
  --from-beginning `
  --property value.deserializer=org.apache.kafka.common.serialization.StringDeserializer
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
