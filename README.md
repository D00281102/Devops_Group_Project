# DevOps Group Project

# Sensor Simulator

## Overview

The Python Sensor Simulator is used to simulate live IoT sensor devices using an existing IoT telemetry dataset.

The simulator reads the dataset row-by-row, converts each sensor reading into JSON, replays the readings using the timing information contained in the original dataset, and publishes each simulated reading to an MQTT broker.

The current data flow is:

```text
IoT Telemetry CSV Dataset
        ↓
Python Sensor Simulator
        ↓
JSON Message
        ↓
MQTT Broker (Eclipse Mosquitto)
        ↓
sensors/telemetry
        ↓
MQTT Subscriber / Other Project Components
```

The MQTT broker is currently running locally for prototype testing.

---

## Dataset

The simulator uses the selected IoT telemetry dataset:

```text
iot_telemetry_data.csv
```

The dataset contains approximately 405,000 sensor readings from three IoT devices.

The dataset contains the following fields:

- `ts` - Timestamp of the sensor reading
- `device` - Device identifier
- `co` - Carbon monoxide reading
- `humidity` - Humidity reading
- `light` - Light sensor state
- `lpg` - LPG gas reading
- `motion` - Motion sensor state
- `smoke` - Smoke reading
- `temp` - Temperature reading

The dataset should be stored locally at:

```text
Prototype/data/iot_telemetry_data.csv
```

The `data` directory is excluded from GitHub using `.gitignore` because the dataset is large.

The `.gitignore` contains:

```text
Prototype/data/
__pycache__/
```

Therefore, anyone cloning the repository must obtain the dataset separately and place it in:

```text
Prototype/data/
```

---

## Project Structure

The relevant project structure is:

```text
Devops_Group_Project/
│
├── Prototype/
│   ├── data/
│   │   └── iot_telemetry_data.csv
│   │
│   ├── Data_Sensor.py
│   └── requirements.txt
│
├── .gitignore
└── README.md
```

---

# Requirements

The simulator requires:

- Python 3
- Eclipse Mosquitto MQTT Broker
- `paho-mqtt` Python package

The Python dependency is stored in:

```text
Prototype/requirements.txt
```

The contents of `requirements.txt` are:

```text
paho-mqtt
```

---

# Installing Python Dependencies

From the root directory of the project, run:

```powershell
py -m pip install -r Prototype/requirements.txt
```

Alternatively, `paho-mqtt` can be installed directly using:

```powershell
py -m pip install paho-mqtt
```

A successful installation should show output similar to:

```text
Successfully installed paho-mqtt
```

---

# Eclipse Mosquitto Setup

The simulator currently uses Eclipse Mosquitto as the local MQTT broker.

Current MQTT configuration:

```text
Broker: localhost
Port: 1883
Topic: sensors/telemetry
```

The broker is currently configured for local prototype testing.

This means:

```text
localhost
```

refers to the computer running the simulator.

The broker address may need to be changed later when the different group project components are integrated.

---

## Mosquitto on Windows

Mosquitto is normally installed in:

```text
C:\Program Files\mosquitto\
```

If the `mosquitto` command works from PowerShell, commands can be entered normally.

For example:

```powershell
mosquitto_sub -h localhost -p 1883 -t sensors/telemetry -v
```

If Windows displays:

```text
mosquitto is not recognized
```

use the full executable path instead:

```powershell
& "C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -p 1883 -t sensors/telemetry -v
```

---

# Testing the MQTT Broker

Before running the Python simulator, the MQTT broker can be tested manually.

## Step 1 - Start an MQTT Subscriber

Open a PowerShell terminal and enter:

```powershell
& "C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -p 1883 -t sensors/telemetry -v
```

The terminal may initially display nothing.

This is expected because the subscriber is waiting for an MQTT message.

Leave this terminal running.

---

## Step 2 - Publish a Test Message

Open another PowerShell terminal and run:

```powershell
& "C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -p 1883 -t sensors/telemetry -m "MQTT test message"
```

The subscriber terminal should then display:

```text
sensors/telemetry MQTT test message
```

This confirms that the following connection works correctly:

```text
MQTT Publisher
      ↓
Mosquitto Broker
      ↓
MQTT Subscriber
```

---

# Python Sensor Simulator

The sensor simulator is located at:

```
Prototype/Data_Sensor.py
```

# How the Simulator Works

Each row in the CSV dataset represents a sensor reading.

For every row, the simulator performs the following steps:

1. Reads the next row from the CSV dataset.
2. Converts numeric CSV values from strings into numbers.
3. Converts `light` and `motion` into Boolean values.
4. Creates a structured Python sensor message.
5. Converts the sensor message into JSON.

---

# Kafka Integration

Kafka is used as a second-stage messaging system after MQTT. The Python sensor does not publish directly to Kafka. Kafka Connect subscribes to MQTT and forwards the MQTT messages to Kafka.

The complete data flow is:

```text
CSV Dataset
     ↓
Data_Sensor.py
     ↓ MQTT: sensors/telemetry
Eclipse Mosquitto (localhost:1883)
     ↓
Kafka Connect MQTT Source Connector
     ↓ Kafka: sensor-telemetry
Apache Kafka Broker (localhost:9092)
     ↓
Kafka Consumer
```

## Kafka Components

The local prototype uses:

- Apache Kafka `2.13-3.6.1`
- Kafka broker on `localhost:9092`
- Kafka Connect REST API on `localhost:8083`
- MQTT broker on `localhost:1883`
- MQTT source connector class `io.confluent.connect.mqtt.MqttSourceConnector`
- MQTT source connector version `1.7.9`
- Kafka topic `sensor-telemetry`

Kafka broker, Kafka Connect, Mosquitto, the consumer, and the sensor are separate processes. Run each long-running process in its own VS Code PowerShell terminal.

## Kafka Connect Plugin Setup

Kafka Connect needs an MQTT source connector plugin. The connector package includes the main connector JAR and its dependency JARs.

Download the Confluent Platform file Here:
[Confluent Platform](https://www.confluent.io/hub/confluentinc/kafka-connect-mqtt)

The current local plugin layout is:

```text
C:\kafka\plugins\
└── confluentinc-kafka-connect-mqtt-1.7.9\
     ├── kafka-connect-mqtt-1.7.9.jar
     ├── org.eclipse.paho.client.mqttv3-1.2.5.jar
     └── other connector dependency JARs
```

All JAR files for this connector must be in the same plugin directory. Kafka Connect is configured in `C:\kafka\config\connect-distributed.properties` with:

```properties
plugin.path=C:/kafka/plugins
```

After changing the plugin files or this setting, restart Kafka Connect.

## Starting the Services

Start the services in this order. Keep each command running in its own terminal.

### 1. Start Mosquitto

In the terminal named `mqtt broker`:

```powershell
& "C:\Program Files\mosquitto\mosquitto.exe" -v
```

### 2. Start Kafka

In the terminal named `kafka broker`:

```powershell
Set-Location "C:\kafka"
.\bin\windows\kafka-server-start.bat .\config\kraft\server.properties
```

Kafka must be running before Kafka Connect starts.

### 3. Start Kafka Connect

In the terminal named `kafka connect`:

```powershell
Set-Location "C:\kafka"
.\bin\windows\connect-distributed.bat .\config\connect-distributed.properties
```

Kafka Connect should remain running and listen on port `8083`.

### 4. Start an MQTT Subscriber

In the terminal named `mosquitto_sub`:

```powershell
& "C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -p 1883 -t sensors/telemetry -v
```

### 5. Start a Kafka Consumer

In the terminal named `kafka consumer`:

```powershell
Set-Location "C:\kafka"
.\bin\windows\kafka-console-consumer.bat --bootstrap-server localhost:9092 --topic sensor-telemetry --from-beginning
```

### 6. Start the Sensor

In the terminal named `sensor`:

```powershell
Set-Location "C:\Devops_Group_Project"
py .\Prototype\Data_Sensor.py
```

## Verify Kafka Connect

Use a separate PowerShell terminal for these commands.

Check that Kafka Connect is responding:

```powershell
Invoke-RestMethod http://localhost:8083/
```

Check that the MQTT connector is loaded:

```powershell
Invoke-RestMethod http://localhost:8083/connector-plugins
```

The response should include:

```text
io.confluent.connect.mqtt.MqttSourceConnector
```

## Register the MQTT Connector

Run this in a separate PowerShell terminal after Kafka, Mosquitto, and Kafka Connect are running:

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
          "value.converter" = "org.apache.kafka.connect.storage.StringConverter"
     }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
     -Method Post `
     -Uri "http://localhost:8083/connectors" `
     -ContentType "application/json" `
     -Body $body
```

The replication factor is `1` because this prototype uses one Kafka broker.

Confirm that the connector was registered:

```powershell
Invoke-RestMethod http://localhost:8083/connectors
```

Check the connector and task status:

```powershell
Invoke-RestMethod http://localhost:8083/connectors/mqtt-source/status
```

The connector and task should both report:

```text
RUNNING
```

## Expected Results

When the sensor is running:

- `mosquitto_sub` displays messages on `sensors/telemetry`.
- The Kafka Connect connector reads those MQTT messages.
- The Kafka consumer displays records from `sensor-telemetry`.
- The original sensor JSON is forwarded as the Kafka record value.

## Troubleshooting

Check Kafka before checking Kafka Connect:

```powershell
Test-NetConnection localhost -Port 9092
```

The result should contain:

```text
TcpTestSucceeded : True
```

If `/connectors` returns an empty list, the MQTT connector has not been registered yet. If `/connector-plugins` does not list `MqttSourceConnector`, check `plugin.path`, confirm the connector JARs are present, and restart Kafka Connect.

If connector registration reports `Missing required configuration "confluent.topic.bootstrap.servers"`, add `confluent.topic.bootstrap.servers=localhost:9092` and `confluent.topic.replication.factor=1` to the connector configuration.

If the Kafka consumer is blank, first confirm that `mosquitto_sub` receives messages, then check the MQTT connector status. A blank consumer does not necessarily indicate an error; it may simply be waiting for a Kafka record.

Stop the services with `Ctrl+C` in the reverse order of startup. Do not delete or reformat Kafka storage for a normal restart.
6. Calculates the time difference between the current reading and the previous reading.
7. Uses this difference to simulate the original sensor timing.
8. Speeds the replay up using the `REPLAY_SPEED` value.
9. Publishes the JSON message to the MQTT broker.
10. Displays the simulated reading in the terminal.

---

# Replay Speed

The simulator currently contains:

```python
REPLAY_SPEED = 10
```

This means the dataset is replayed approximately ten times faster than the original data.

For example, if two readings originally occurred five seconds apart:

```text
Original delay: 5 seconds
Replay speed: 10
Simulator delay: 0.5 seconds
```

This allows the project to demonstrate the sensor data without waiting for the complete original time period.

---

# Maximum Readings

During prototype testing, the simulator is limited to:

```python
MAX_READINGS = 10
```

This means the program currently publishes ten readings and then stops.

This is useful for testing and demonstration.

The limit can later be increased or removed if continuous dataset replay is required.

---

# Running the Sensor Simulator

First, make sure:

1. Mosquitto is running.
2. The dataset is located at:

```
Prototype/data/iot_telemetry_data.csv
```

3. Python dependencies have been installed.

From the root of the project run:

```powershell
py Prototype/Data_Sensor.py
```

---

# Expected Simulator Output

The Python terminal should first display:

```text
Connected to MQTT broker: localhost:1883
Starting IoT sensor simulation...
```

For each reading it should display:

```text
Published to MQTT topic: sensors/telemetry
Simulated reading 1:
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

The simulator continues until the configured number of readings has been processed.

After ten readings it should display:

```text
Sensor simulation complete.
```

---

# JSON Message Format

Each MQTT message contains one simulated sensor reading.

Example:

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

The JSON message contains all sensor values from the original dataset.

---

# Testing Published Sensor Messages

To confirm that the Python program is actually publishing messages through MQTT rather than only printing them locally, open another terminal.

Run:

```powershell
& "C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -p 1883 -t sensors/telemetry -v
```

Leave this subscriber running.

Then run the Python simulator in another terminal:

```powershell
py Prototype/Data_Sensor.py
```

---

# Expected MQTT Subscriber Output

The subscriber should receive messages similar to:

```text
sensors/telemetry {"ts": 1594512094.3859746, "device": "b8:27:eb:bf:9d:51", "co": 0.004955938648391245, "humidity": 51.0, "light": false, "lpg": 0.00765082227055719, "motion": false, "smoke": 0.02041127012241292, "temp": 22.7}
```

Further readings should continue appearing:

```text
sensors/telemetry {"ts": 1594512094.7355676, "device": "00:0f:00:70:91:0a", "co": 0.0028400886071015706, "humidity": 76.0, "light": false, "lpg": 0.005114383400977071, "motion": false, "smoke": 0.013274836704851536, "temp": 19.700000762939453}
```

This confirms the following complete flow:

```text
CSV Dataset
     ↓
Data_Sensor.py
     ↓
Sensor Reading
     ↓
JSON
     ↓
MQTT Publish
     ↓
Mosquitto Broker
     ↓
sensors/telemetry
     ↓
MQTT Subscriber
```

---

# MQTT Integration

Other components of the group project that require sensor data should subscribe to:

```text
sensors/telemetry
```

They should expect messages using the JSON structure documented above.

For example, another project component could subscribe to the MQTT topic and forward the messages to Kafka.

The Sensor Simulator itself is responsible for:

```text
Dataset
    ↓
Sensor Simulation
    ↓
JSON
    ↓
MQTT
```

Further processing after MQTT is handled by the relevant group project components.

---

# Current Prototype Configuration

The current prototype configuration is:

```text
Dataset:
Prototype/data/iot_telemetry_data.csv

Python Simulator:
Prototype/Data_Sensor.py

MQTT Broker:
localhost

MQTT Port:
1883

MQTT Topic:
sensors/telemetry

Replay Speed:
10x

Test Reading Limit:
10
```

---

# Troubleshooting

## Mosquitto command not recognised

If this command:

```powershell
mosquitto_sub
```

returns:

```text
The term 'mosquitto_sub' is not recognized
```

use:

```powershell
& "C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -p 1883 -t sensors/telemetry -v
```

---

## MQTT port 1883 already in use

If attempting to manually start Mosquitto produces an error similar to:

```text
Error: Only one usage of each socket address
(protocol/network address/port) is normally permitted.
```

this usually means a Mosquitto broker is already running on port `1883`.

Do not start another broker.

Test the existing broker using:

```powershell
& "C:\Program Files\mosquitto\mosquitto_sub.exe" -h localhost -p 1883 -t sensors/telemetry -v
```

and:

```powershell
& "C:\Program Files\mosquitto\mosquitto_pub.exe" -h localhost -p 1883 -t sensors/telemetry -m "MQTT test message"
```

If the subscriber displays:

```text
sensors/telemetry MQTT test message
```

the broker is already running correctly.

---

## Dataset not found

If Python reports that:

```text
iot_telemetry_data.csv
```

cannot be found, check that the file exists at:

```text
Prototype/data/iot_telemetry_data.csv
```

The dataset is deliberately excluded from GitHub, so it must be added locally.

---

## paho-mqtt not installed

If Python displays:

```text
ModuleNotFoundError: No module named 'paho'
```

install the required package:

```powershell
py -m pip install -r Prototype/requirements.txt
```

Then run the simulator again:

```powershell
py Prototype/Data_Sensor.py
```

---

# Prototype Status

The Sensor Simulator has been tested successfully with:

- CSV dataset reading
- Conversion of CSV values into correct Python data types
- JSON message generation
- Timestamp-based sensor replay
- Accelerated replay timing
- MQTT broker connection
- MQTT publishing
- MQTT subscription
- Successful receipt of simulated JSON sensor readings

The current prototype successfully demonstrates:

```text
IoT Dataset
     ↓
Python Sensor Simulator
     ↓
Timed JSON Sensor Readings
     ↓
Eclipse Mosquitto MQTT Broker
     ↓
MQTT Subscriber / Project Integration
```




This document contains everything you need to connect to the shared PostgreSQL
database that holds the `green_ai_datacenter` dataset.

---
The following were already done before the steps in this document:

  - PostgreSQL 17 installed on Windows.
  - TimescaleDB 2.30.1 installed (files copied into lib and
    share\extension).
  - shared_preload_libraries = 'timescaledb' set in postgresql.conf.
  - Extension registered in the postgres database.
  - PostgreSQL service running on port 5432.
  - Host machine LAN IP: 192.168.1.8

This log picks up from there — the point where the green_ai_datacenter
dataset needs to be loaded.
------------------------------------------------------------------------
------------------------------------------------------------------------
Everything needed to run this project on your own machine locally.
------------------------------------------------------------------------
1. PREREQUISITES
------------------------------------------------------------------------

Install these before anything else:

  - PostgreSQL 17 for Windows
      Download: https://www.postgresql.org/download/windows/
      Installer will ask for a password for the "postgres" user —
      REMEMBER IT.

  - Microsoft Visual C++ Redistributable (2015-2022)
      Download: https://aka.ms/vs/17/release/vc_redist.x64.exe

  - OpenSSL v3.x (required by TimescaleDB)
      Download: https://slproweb.com/products/Win32OpenSSL.html
      Pick the 64-bit v3.x installer.

  - TimescaleDB Windows zip matching PostgreSQL 17
      Download from the TimescaleDB GitHub releases page.
      Pick the file named something like:
        timescaledb-postgresql-17-windows-amd64.zip

------------------------------------------------------------------------
2. INSTALL TIMESCALEDB
------------------------------------------------------------------------

Step 1 — Stop PostgreSQL

    Windows key -> Services -> postgresql-x64-17 -> Stop

Step 2 — Extract the TimescaleDB zip

    Right-click the zip -> Extract All.
    You should end up with a folder containing:
      setup.exe
      timescaledb-2.30.1.dll
      timescaledb-tsl-2.30.1.dll
      timescaledb.dll
      timescaledb.control
      timescaledb-tune.exe
      ~69 .sql files

Step 3 — Add PostgreSQL to PATH

    Windows key -> sysdm.cpl -> Advanced -> Environment Variables
    Under SYSTEM variables, select Path -> Edit -> New
    Add:
        C:\Program Files\PostgreSQL\17\bin
    OK on all dialogs.

Step 4 — Open a NEW Administrator Command Prompt

    Windows key -> cmd -> right-click -> Run as administrator.

Step 5 — Verify PATH

    pg_config

    Should return output. If it says "not recognized", the PATH edit
    didn't take — redo step 3.

Step 6 — Run the TimescaleDB setup

    cd "C:\path\to\extracted\timescaledb"
    setup.exe

    When prompted:
      - Y to proceed
      - Paste the config path:
          C:\Program Files\PostgreSQL\17\data\postgresql.conf
      - Y to update shared_preload_libraries
      - n to skip timescaledb-tune (optional)

Step 7 — If the setup fails with "Access is denied"

    Manually copy the files from an Administrator Command Prompt:

      copy "C:\path\to\extracted\timescaledb\*.dll" "C:\Program Files\PostgreSQL\17\lib\"
      copy "C:\path\to\extracted\timescaledb\*.sql" "C:\Program Files\PostgreSQL\17\share\extension\"
      copy "C:\path\to\extracted\timescaledb\timescaledb.control" "C:\Program Files\PostgreSQL\17\share\extension\"

Step 8 — Start PostgreSQL

    Windows key -> Services -> postgresql-x64-17 -> Start

Step 9 — Enable the extension

    psql -U postgres -p 5432 -d postgres -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

    Should print: CREATE EXTENSION

Step 10 — Verify

    psql -U postgres -p 5432 -d postgres -c "SELECT extname, extversion FROM pg_extension WHERE extname='timescaledb';"

    Should print:
        extname   | extversion
    -------------+------------
     timescaledb | 2.30.1

------------------------------------------------------------------------
3. LOAD THE DATASET
------------------------------------------------------------------------

Step 1 — Connect to psql

    psql -U postgres -p 5432

    Enter your password. You should land at: postgres=#

------------------------------------------------------------------------
4. TABLE CREATION
------------------------------------------------------------------------

WHERE: inside the psql prompt (postgres=#).

    CREATE TABLE green_ai_datacenter (
        records integer GENERATED ALWAYS AS IDENTITY,
        server_type text,
        cooling_type text,
        datacenter_region text,
        time_of_day text,
        maintenance_status text,
        energy_source_primary text,
        server_age_years integer,
        rack_u_position integer,
        workload_intensity double precision,
        cpu_utilization double precision,
        gpu_utilization double precision,
        memory_utilization double precision,
        storage_utilization double precision,
        disk_io_iops double precision,
        network_throughput_gbps double precision,
        network_latency_ms double precision,
        virtual_machines_count integer,
        ambient_temperature_c double precision,
        humidity_percentage double precision,
        inlet_temperature_c double precision,
        exhaust_temperature_c double precision,
        fan_speed_rpm double precision,
        airflow_cfm double precision,
        cooling_efficiency double precision,
        power_supply_efficiency double precision,
        ups_battery_health double precision,
        power_consumption_kw double precision,
        pue double precision,
        wue double precision,
        carbon_intensity_gco2_kwh double precision,
        renewable_energy_ratio double precision,
        carbon_emission_kg double precision,
        compute_cost_usd double precision,
        energy_efficiency_class text,
        failure_risk_level text
    );

NOTES:
  - records uses GENERATED ALWAYS AS IDENTITY — PostgreSQL auto-numbers
    it 1, 2, 3, ...
  - Column order matches the CSV so the load lines up.
  - The records column is NOT present in the CSV.
  - Types were chosen to match the CSV contents: text for string
    columns, integer for whole numbers, double precision for decimals.

RESULT: CREATE TABLE

------------------------------------------------------------------------
5. CSV LOAD
------------------------------------------------------------------------

WHERE: inside the same psql prompt.

    \copy green_ai_datacenter (server_type, cooling_type,
    datacenter_region, time_of_day, maintenance_status,
    energy_source_primary, server_age_years, rack_u_position,
    workload_intensity, cpu_utilization, gpu_utilization,
    memory_utilization, storage_utilization, disk_io_iops,
    network_throughput_gbps, network_latency_ms,
    virtual_machines_count, ambient_temperature_c,
    humidity_percentage, inlet_temperature_c, exhaust_temperature_c,
    fan_speed_rpm, airflow_cfm, cooling_efficiency,
    power_supply_efficiency, ups_battery_health, power_consumption_kw,
    pue, wue, carbon_intensity_gco2_kwh, renewable_energy_ratio,
    carbon_emission_kg, compute_cost_usd, energy_efficiency_class,
    failure_risk_level)
    FROM 'C:\Users\jo2kk\Downloads\green_ai_datacenter.csv'
    WITH (FORMAT csv, HEADER true);

NOTES:
  - \copy (with backslash) reads the file FROM THE MACHINE RUNNING PSQL,
    not from the server.
  - The column list OMITS records so PostgreSQL generates it.
  - HEADER true skips the CSV header row.
  - The CSV path is the full path to the file on the local machine.

RESULT: COPY 100000

------------------------------------------------------------------------
6. VERIFICATION QUERIES
------------------------------------------------------------------------

WHERE: inside the same psql prompt.

Row count:

    SELECT COUNT(*) FROM green_ai_datacenter;

RESULT: 100000

Spot-check that the identity column worked:

    SELECT records, server_type, cpu_utilization
    FROM green_ai_datacenter
    ORDER BY records
    LIMIT 5;

RESULT:

     records | server_type | cpu_utilization
    ---------+-------------+-----------------
           1 | Edge        |          46.498
           2 | GPU         |          21.285
           3 | Compute     |          52.201
           4 | Compute     |          32.406
           5 | GPU         |          27.067
    (5 rows)

WHAT THIS CONFIRMS: 100,000 rows loaded; the auto-generated records
column numbered them 1 through 100,000, and values landed in the correct
columns.

------------------------------------------------------------------------
7. NETWORK EXPOSURE FOR THE TEAM
------------------------------------------------------------------------

Two config files were edited to allow teammates on the LAN to connect.
Both are in C:\Program Files\PostgreSQL\17\data\.

FILE 1: postgresql.conf
Find the line listen_addresses and change it to:

    listen_addresses = '*'

FILE 2: pg_hba.conf

Add at the bottom:

    host    all    all    192.168.1.0/24    md5

THEN RESTART THE SERVICE:

    Windows key -> Services -> postgresql-x64-17 -> Restart

NOTES:
  - listen_addresses = '*' tells PostgreSQL to accept connections on all
    network interfaces, not just localhost.
  - The pg_hba.conf line allows any user to connect to any database from
    any machine in the 192.168.1.x range, using a password (md5).
  - Never use trust for network connections — it means anyone on the LAN
    can log in without a password.
  - The service MUST be restarted for either change to take effect.

------------------------------------------------------------------------
8. FINAL ENVIRONMENT SUMMARY
------------------------------------------------------------------------

    Item                       | Value
    ---------------------------+--------------------------------------
    PostgreSQL version         | 17
    PostgreSQL service name    | postgresql-x64-17
    PostgreSQL port            | 5432
    TimescaleDB version        | 2.30.1
    Host machine LAN IP        | 192.168.1.8
    Database                   | postgres
    Table                      | green_ai_datacenter
    Rows loaded                | 100,000
    Columns                    | 38 (incl. auto records)
    shared_preload_libraries   | 'timescaledb'
    Extension installed        | yes (CREATE EXTENSION run)
    Table type                 | regular table (not a hypertable)
    Timestamp column           | none — required if converting to
                               | hypertable
    Team LAN range allowed     | 192.168.1.0/24

------------------------------------------------------------------------
9. CONNECTION STRING FOR TEAMMATES
------------------------------------------------------------------------

    postgresql://postgres:YOUR_PASSWORD@192.168.1.8:5432/postgres

  - Port is 5432, not the default-adjacent 5434 that was used during
    setup.
  - Password is shared separately, not in this file.
  - Table name for queries and connectors: green_ai_datacenter.

## 1. Connection Details

| Item           | Value                                              |
|----------------|----------------------------------------------------|
| Host           | `192.168.1.8` (LAN IP — update if it changes)      |
| Port           | `5434`                                             |
| Database       | `postgres`                                         |
| User           | `postgres`                                         |
| Password       | *(ask the DB owner — not stored in this repo)*     |
| Table          | `green_ai_datacenter`                              |
| Rows           | 100,000                                            |
| TimescaleDB    | Installed (v2.30.1), but table is a regular table  |

**Connection string (for Python, JDBC, etc.):**


> The port is **5434**, not the default 5432. Do not omit it.

---

## 2. Table Schema

The table has 38 columns. The first column, `records`, is auto-generated.

| Column                     | Type              | Notes                          |
|----------------------------|-------------------|--------------------------------|
| `records`                  | integer           | Auto-generated (1 … 100,000)   |
| `server_type`              | text              | Edge / GPU / Compute / Storage |
| `cooling_type`             | text              | Air / Liquid / Hybrid          |
| `datacenter_region`        | text              | EU / NA / APAC / ME            |
| `time_of_day`              | text              | Night / Peak / Off-Peak        |
| `maintenance_status`       | text              | Normal / Recent / Pending      |
| `energy_source_primary`    | text              | Solar / Grid / Wind / Hydro    |
| `server_age_years`         | integer           |                                |
| `rack_u_position`          | integer           |                                |
| `workload_intensity`       | double precision  |                                |
| `cpu_utilization`          | double precision  |                                |
| `gpu_utilization`          | double precision  |                                |
| `memory_utilization`       | double precision  |                                |
| `storage_utilization`      | double precision  |                                |
| `disk_io_iops`             | double precision  |                                |
| `network_throughput_gbps`  | double precision  |                                |
| `network_latency_ms`       | double precision  |                                |
| `virtual_machines_count`   | integer           |                                |
| `ambient_temperature_c`    | double precision  |                                |
| `humidity_percentage`      | double precision  |                                |
| `inlet_temperature_c`      | double precision  |                                |
| `exhaust_temperature_c`    | double precision  |                                |
| `fan_speed_rpm`            | double precision  |                                |
| `airflow_cfm`              | double precision  |                                |
| `cooling_efficiency`       | double precision  |                                |
| `power_supply_efficiency`  | double precision  |                                |
| `ups_battery_health`       | double precision  |                                |
| `power_consumption_kw`     | double precision  |                                |
| `pue`                      | double precision  |                                |
| `wue`                      | double precision  |                                |
| `carbon_intensity_gco2_kwh`| double precision  |                                |
| `renewable_energy_ratio`   | double precision  |                                |
| `carbon_emission_kg`       | double precision  |                                |
| `compute_cost_usd`         | double precision  |                                |
| `energy_efficiency_class`  | text              | High / Medium / Low            |
| `failure_risk_level`       | text              | Low / Medium / High            |

> `records` is `GENERATED ALWAYS AS IDENTITY`. Do **not** insert a value into
> it — PostgreSQL fills it automatically.

---

## 3. For the Kafka Engineer

You are producing/consuming messages that will be written to the
`green_ai_datacenter` table (or read from it).

- **Do not include the `records` column** in anything you send. It is managed by PostgreSQL.
- Your JDBC sink connector will need:
  - `connection.url` → `jdbc:postgresql://192.168.1.8:5434/postgres`
  - `connection.user` → `postgres`
  - `connection.password` → *(get from DB owner)*
- Kafka Connect JDBC sink does **not** support `GENERATED ALWAYS AS IDENTITY` in
  `insert.mode=upsert` cleanly. Use `insert.mode=insert` if you are only adding
  new rows, or drop the identity behaviour if you need upserts.
- The table name for the connector is `green_ai_datacenter`.

---

## 4. For the Visualisation Engineer

You only need **read access**.

- Connect your tool (Confluent, Metabase, Grafana, Tableau, whatever) using the
  connection string in section 1.
- Example starting query:
  ```sql
  SELECT *
  FROM green_ai_datacenter
  ORDER BY records
  LIMIT 100;

Useful syntax query to do own test.
-- Average PUE by region
SELECT datacenter_region, AVG(pue) AS avg_pue
FROM green_ai_datacenter
GROUP BY datacenter_region;

-- Carbon emissions by energy source
SELECT energy_source_primary, SUM(carbon_emission_kg) AS total_kg
FROM green_ai_datacenter
GROUP BY energy_source_primary;


---

# Kafka to Database Integration

The Kafka to Database component reads sensor messages from the Kafka topic and stores them in PostgreSQL.

The current flow is:

```text
Kafka topic: sensor-telemetry
        ↓
kafka_to_database.py
        ↓
JSON sensor data
        ↓
PostgreSQL / TimescaleDB
