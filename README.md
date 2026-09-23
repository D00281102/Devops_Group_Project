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

```text
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