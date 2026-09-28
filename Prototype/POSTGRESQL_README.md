# PostgreSQL Database Integration

## Overview

My part of the prototype focuses on the PostgreSQL database side of the project.

I first created a small local database using a sample of the IoT telemetry dataset. This was used to test the database structure, sensor data types, inserts and basic SQL queries before working with the full shared database.

I also created a Python Kafka consumer that reads sensor messages from the `sensor-telemetry` Kafka topic and stores the readings in PostgreSQL.

The current data flow for this part is:

```text
Kafka Topic: sensor-telemetry
        |
        v
kafka_to_database.py
        |
        v
PostgreSQL Database
        |
        v
IoT Sensor Data
```

---

## PostgreSQL and TimescaleDB Setup

For the first database prototype, I used:

- PostgreSQL 17
- TimescaleDB
- pgAdmin 4
- Database: `iot_sensor_db`
- Table: `sensor_data`

The database was created locally first so that the IoT sensor data structure could be tested before connecting it to the other parts of the prototype.

TimescaleDB was enabled in the database using:

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

## Database Structure

The `sensor_data` table was created using the columns from the IoT telemetry dataset:

```sql
CREATE TABLE sensor_data (
    id BIGSERIAL,
    ts TIMESTAMPTZ NOT NULL,
    device TEXT,
    co DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    light BOOLEAN,
    lpg DOUBLE PRECISION,
    motion BOOLEAN,
    smoke DOUBLE PRECISION,
    temp DOUBLE PRECISION,
    PRIMARY KEY (id, ts)
);
```

The table was converted into a TimescaleDB hypertable using the `ts` column:

```sql
SELECT create_hypertable('sensor_data', 'ts');
```

This allowed the prototype database to store the IoT readings as time-series data.

---

## Testing with Sample Sensor Data

Before using live data from Kafka, I tested the database using a small sample of sensor readings.

Three sample readings using the same fields as the IoT telemetry dataset were inserted into the `sensor_data` table. This was used to confirm that PostgreSQL accepted the sensor values and that the table structure was working correctly.

The stored readings were checked using:

```sql
SELECT * FROM sensor_data;
```

The number of readings was checked using:

```sql
SELECT COUNT(*) FROM sensor_data;
```

The latest readings can be retrieved using:

```sql
SELECT *
FROM sensor_data
ORDER BY ts DESC
LIMIT 5;
```

Readings can also be filtered by device:

```sql
SELECT *
FROM sensor_data
WHERE device = 'DEVICE_ID'
ORDER BY ts DESC;
```

These tests confirmed that the local prototype could store and retrieve the IoT sensor data correctly.

---

## Kafka to PostgreSQL Integration

After testing the database with sample data, I created a Python Kafka consumer to store sensor readings coming from Kafka.

The consumer is located at:

```text
Prototype/kafka_to_database.py
```

It listens to:

```text
sensor-telemetry
```

The flow is:

```text
IoT Sensor Dataset
        |
        v
Sensor Simulator
        |
        v
MQTT
        |
        v
Kafka
        |
        v
sensor-telemetry
        |
        v
kafka_to_database.py
        |
        v
PostgreSQL
        |
        v
sensor_data
```

### How the Consumer Works

The consumer:

1. Connects to the `sensor-telemetry` Kafka topic.
2. Waits for a sensor message.
3. Decodes the Kafka message from bytes into UTF-8 text.
4. Converts the JSON message into a Python object.
5. Converts the Unix `ts` value into a UTC PostgreSQL timestamp.
6. Inserts the sensor values into the `sensor_data` table.
7. Commits the transaction.

If an error occurs, the transaction is rolled back and the error is printed in the terminal.

---

## Python Requirements

The Python packages are stored in:

```text
Prototype/requirements.txt
```

The current requirements are:

```text
paho-mqtt
kafka-python
psycopg2-binary
```

For this component, `kafka-python` is used to consume Kafka messages and `psycopg2-binary` is used to connect Python to PostgreSQL.

Install the requirements from the project root with:

```powershell
py -m pip install -r Prototype/requirements.txt
```

---

## Local Database Connection

For local testing, the consumer connects to:

```text
Host: localhost
Port: 5432
Database: iot_sensor_db
User: postgres
Table: sensor_data
```

The PostgreSQL password is not stored in the Python file. The program asks for it when it starts using Python's `getpass` module.

---

## Kafka Configuration

The local consumer uses:

```text
Kafka Broker: localhost:9092
Kafka Topic: sensor-telemetry
Consumer Group: database-consumer
```

The consumer configuration in `kafka_to_database.py` is:

```python
consumer = KafkaConsumer(
    "sensor-telemetry",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="latest",
    group_id="database-consumer"
)
```

---

## Sensor Message Format

The consumer expects the sensor message to contain these fields:

```json
{
    "ts": 1594512094.3859746,
    "device": "b8:27:eb:bf:9d:51",
    "co": 0.004955938648391245,
    "humidity": 51.0,
    "light": false,
    "lpg": 0.00765082227055719,
    "motion": false,
    "smoke": 0.02041127012241292,
    "temp": 22.7
}
```

The values are inserted into the matching PostgreSQL columns.

---

## Timestamp Conversion

The IoT dataset provides `ts` as a Unix timestamp.

For the local prototype, the consumer converts it into a UTC timestamp before inserting it:

```python
timestamp = datetime.fromtimestamp(
    float(data["ts"]),
    tz=timezone.utc
)
```

This matches the `TIMESTAMPTZ` column used by the local `sensor_data` table.

---

## Running the Consumer

Before running the consumer, make sure:

1. PostgreSQL is running.
2. `iot_sensor_db` exists.
3. The `sensor_data` table exists.
4. Kafka is running on `localhost:9092`.
5. The `sensor-telemetry` topic is available.
6. The Python requirements are installed.

From the project root, run:

```powershell
py Prototype/kafka_to_database.py
```

The program asks for the PostgreSQL password and then displays:

```text
Kafka -> Database consumer started.
Waiting for sensor data...
```

When a valid sensor reading is stored, it displays:

```text
Stored sensor reading from DEVICE_ID
```

---

## Kafka to PostgreSQL Test

The local integration was tested using a sensor message with the device name:

```text
kafka-db-proof
```

The consumer displayed:

```text
Stored sensor reading from kafka-db-proof
```

The database was then checked with:

```sql
SELECT *
FROM sensor_data
WHERE device = 'kafka-db-proof';
```

The test record was returned from PostgreSQL. This confirmed that the local Kafka-to-PostgreSQL flow was working.

---

## Shared Database Integration

The local database was created to test the PostgreSQL structure and Kafka integration independently.

The group is also working on a shared PostgreSQL database containing the full IoT telemetry dataset. The shared setup currently uses the `iot_telemetry_data` table.

The shared schema differs from the local prototype. In particular, the shared setup uses a different database/table configuration and stores `ts` as a Unix timestamp value rather than the local `TIMESTAMPTZ` format.

The final shared-database connection and Kafka-to-database test still need to be verified with the shared database setup.

Database passwords must not be stored in this repository.

---

## Troubleshooting

### PostgreSQL Connection Error

Check that PostgreSQL is running and that the local connection details are correct:

```text
Host: localhost
Port: 5432
Database: iot_sensor_db
User: postgres
```

### Consumer Waiting for Data

If the program displays:

```text
Kafka -> Database consumer started.
Waiting for sensor data...
```

but no readings appear, check that Kafka is running and that new messages are being sent to `sensor-telemetry`.

### JSON Error

The consumer expects valid JSON containing:

```text
ts
device
co
humidity
light
lpg
motion
smoke
temp
```

A plain-text or incorrectly formatted Kafka record cannot be processed as a sensor reading.

### Database Insert Error

If a message is received but cannot be inserted, check the PostgreSQL connection, table name, column names, message fields and timestamp format.

The consumer rolls back the transaction when an error occurs.

---

## Current Status

The local PostgreSQL prototype has been tested with:

- PostgreSQL 17 and TimescaleDB
- `iot_sensor_db`
- `sensor_data`
- sample IoT readings
- basic SQL queries
- a TimescaleDB hypertable
- a Python PostgreSQL connection
- Kafka sensor messages
- Kafka-to-PostgreSQL inserts
- SQL verification of a Kafka test record

The local database flow is:

```text
Kafka sensor message
        |
        v
kafka_to_database.py
        |
        v
PostgreSQL insert
        |
        v
sensor_data
        |
        v
SQL verification
```

The next stage is to test the integration against the group's shared PostgreSQL database and update the consumer for the final shared database structure.
