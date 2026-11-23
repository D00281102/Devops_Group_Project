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

## Automated Testing

The project uses Python's built-in `unittest` framework to run automated tests.

### Install Dependencies

From the project root, run:

    python -m pip install -r Prototype/requirements.txt

### Run All Tests

Execute the following command from the project root:

    python -m unittest discover -s Prototype -p "test_*.py" -v

This automatically discovers and runs all test files inside the Prototype directory.

### Test Coverage

The automated tests cover:

- Sensor analytics
- Control API
- Control logic
- MQTT messaging
- Kafka integration
- Database connection handling

### External Services

The tests use mocks for external service connections where appropriate. Live MQTT, Kafka and PostgreSQL services are not required to run the automated test suite.

A successful test run currently reports 47 tests passing.

## Control Settings API

The project includes a Control Settings API for managing the sensor control thresholds.

The settings are stored in the existing PostgreSQL database in a table called `control_settings`.

### Database Setup

Before using the Control Settings API, create the database table using the SQL setup file provided in the Prototype directory.

Run the following command from the Prototype directory:

```powershell
psql -h localhost -p 5432 -U postgres -d postgres -f control_settings.sql
```

Update the connection details if your PostgreSQL configuration uses different values.

The script creates the `control_settings` table and inserts the default settings if no settings row already exists. Existing settings are preserved.

### Default Settings

| Setting | Default Value |
|---|---:|
| Temperature threshold | 25°C |
| Humidity threshold | 70% |
| Light enabled | True |

### API Endpoints

The API provides two endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/control-settings` | Retrieves the saved control settings |
| PUT | `/control-settings` | Updates the saved control settings |

### Validation

The API validates settings before saving them:

- Temperature must be between -50 and 100.
- Humidity must be between 0 and 100.
- Light enabled must be a boolean value.

Invalid settings return HTTP 422.

### Testing

The control settings API is covered by automated tests in `test_control_api.py`.

Run the API tests from the `Prototype` directory:

```powershell
python -m unittest test_control_api -v
```

Run the complete test suite:

```powershell
python -m unittest discover -s . -p "test_*.py" -v
```

The full test suite currently contains 47 passing tests.

## Current Scope

The current Compose file containerizes Kafka and Kafka UI only. A fully containerized setup would also need Compose services for Mosquitto, Kafka Connect, the MQTT connector plugin, the sensor, and the Kafka consumer.
