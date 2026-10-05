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
├── Prototype/
│   ├── data/
│   │   └── iot_telemetry_data.csv
│   │
│   ├── Data_Sensor.py
│   ├── Control_Logic.py
│   ├── Actuator_Simulator.py
│   └── requirements.txt
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

The current local plugin layout is:

```te[Confluent Platform](https://www.confluent.io/hub/confluentinc/kafka-connect-mqtt)
nnect-mqtt-1.7.9.jar
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
     -Uri "http://localhost:808ByteArrayConverter
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

---

# MQTT Control Logic and Actuator Simulator

## Overview

The IoT prototype has been extended to include a control component and an actuator simulator.

The control component receives the JSON sensor readings published by `Data_Sensor.py` through MQTT. It evaluates the incoming sensor values using predefined control rules and determines whether an actuator action is required.

When a control rule is triggered, the control component creates a structured JSON actuator command and publishes it to a second MQTT topic.

The actuator simulator subscribes to this topic, receives the command and simulates the requested actuator action.

The complete control flow is:

```text
IoT Telemetry CSV Dataset
        ↓
Data_Sensor.py
        ↓
JSON Sensor Reading
        ↓
MQTT Broker (Eclipse Mosquitto)
        ↓
sensors/telemetry
        ↓
Control_Logic.py
        ↓
Control Rules
        ↓
JSON Actuator Command
        ↓
MQTT Broker (Eclipse Mosquitto)
        ↓
actuators/commands
        ↓
Actuator_Simulator.py
        ↓
Simulated Actuator Action
```

The MQTT broker is currently running locally for prototype testing.

---

# Control Logic

The control logic is located at:

```text
Prototype/Control_Logic.py
```

The control component connects to the local Eclipse Mosquitto MQTT broker using:

```text
Broker: localhost
Port: 1883
Sensor Topic: sensors/telemetry
Actuator Topic: actuators/commands
```

The control component subscribes to:

```text
sensors/telemetry
```

This is the same MQTT topic used by `Data_Sensor.py` to publish the simulated IoT sensor readings.

---

## How the Control Logic Works

For every sensor reading received through MQTT, the control component performs the following steps:

1. Receives a message from `sensors/telemetry`.
2. Decodes the MQTT message payload.
3. Converts the JSON payload into Python data.
4. Reads the sensor values contained in the message.
5. Evaluates the sensor values against the configured control rules.
6. Determines whether an actuator action is required.
7. Creates a structured actuator command when a rule is triggered.
8. Converts the actuator command into JSON.
9. Publishes the command to `actuators/commands`.
10. Displays the control decision in the terminal.

If none of the configured control conditions are met, the program displays:

```text
Control decision: No action required
```

---

# Control Rules

The current prototype uses three control rules.

```text
Temperature >= 25°C  → Fan ON

Humidity >= 70%      → Dehumidifier ON

Light = True         → Light ON
```

These thresholds are used to demonstrate how incoming IoT sensor readings can automatically produce control actions.

A single sensor reading can trigger more than one actuator.

For example, a reading containing:

```text
Temperature: 27°C
Humidity: 77%
Light: True
```

will trigger:

```text
Fan ON
Dehumidifier ON
Light ON
```

A reading that does not meet any of the configured conditions will return:

```text
No action required
```

---

# Running the Control Logic

Before running the control logic, make sure:

1. Eclipse Mosquitto is running.
2. The `paho-mqtt` Python package has been installed.
3. `Control_Logic.py` exists inside the `Prototype` directory.

From the root directory of the project, run:

```powershell
py Prototype/Control_Logic.py
```

Alternatively, change into the `Prototype` directory:

```powershell
cd Prototype
```

Then run:

```powershell
python Control_Logic.py
```

---

# Expected Control Logic Output

When the control component starts successfully, the terminal should display:

```text
Starting IoT control logic...
Connected to MQTT broker: localhost:1883
Subscribed to MQTT topic: sensors/telemetry
Waiting for sensor readings...
```

The program will then wait for sensor readings to be published.

Start `Data_Sensor.py` in another terminal.

When a sensor reading is received, the control terminal should display:

```text
Sensor reading received:
{
    ...
}
```

If the sensor reading does not trigger a configured rule, the terminal should display:

```text
Control decision: No action required
```

If a control rule is triggered, the terminal should display the control decision.

For example:

```text
Control decisions:
- FAN ON - High temperature detected
Published actuator command to: actuators/commands
```

If several rules are triggered by the same sensor reading, multiple actuator commands are generated.

For example:

```text
Control decisions:
- FAN ON - High temperature detected
Published actuator command to: actuators/commands

- DEHUMIDIFIER ON - High humidity detected
Published actuator command to: actuators/commands

- LIGHT ON - Light detected
Published actuator command to: actuators/commands
```

This confirms that the sensor data has successfully passed from the sensor simulator through MQTT to the control component.

---

# Actuator Command Format

When a control rule is triggered, the control component creates a structured JSON actuator command.

Each command contains:

- `actuator` - The actuator that should respond.
- `action` - The action the actuator should perform.
- `reason` - The sensor condition that caused the action.

For example, a high temperature reading produces:

```json
{
    "actuator": "fan",
    "action": "ON",
    "reason": "High temperature detected"
}
```

A high humidity reading can produce:

```json
{
    "actuator": "dehumidifier",
    "action": "ON",
    "reason": "High humidity detected"
}
```

A light reading can produce:

```json
{
    "actuator": "light",
    "action": "ON",
    "reason": "Light detected"
}
```

These commands are published to:

```text
actuators/commands
```

The sensor readings and actuator commands therefore use separate MQTT topics:

```text
Sensor Data:
sensors/telemetry

Actuator Commands:
actuators/commands
```

---

# Actuator Simulator

The actuator simulator is located at:

```text
Prototype/Actuator_Simulator.py
```

The purpose of the actuator simulator is to represent physical IoT actuators during prototype testing.

No physical fan, dehumidifier or light is required.

Instead, the Python program receives the MQTT actuator command and displays the simulated action in the terminal.

The current simulated actuators are:

```text
Fan
Dehumidifier
Light
```

---

# How the Actuator Simulator Works

The actuator simulator performs the following steps:

1. Connects to the local Eclipse Mosquitto MQTT broker.
2. Subscribes to `actuators/commands`.
3. Waits for actuator commands.
4. Receives the JSON MQTT message.
5. Decodes the JSON command.
6. Reads the actuator, action and reason.
7. Determines which simulated actuator should respond.
8. Displays the requested action in the terminal.

The actuator simulator continues listening for commands until it is manually stopped.

---

# Running the Actuator Simulator

Before running the actuator simulator, make sure the Mosquitto MQTT broker is running.

From the root directory of the project, run:

```powershell
py Prototype/Actuator_Simulator.py
```

Alternatively, change into the `Prototype` directory:

```powershell
cd Prototype
```

Then run:

```powershell
python Actuator_Simulator.py
```

---

# Expected Actuator Simulator Output

When the actuator simulator starts successfully, the terminal should display:

```text
Starting IoT actuator simulator...
Connected to MQTT broker: localhost:1883
Subscribed to MQTT topic: actuators/commands
Waiting for actuator commands...
```

The program will remain running while it waits for commands from `Control_Logic.py`.

When an actuator command is received, output similar to the following should appear:

```text
Actuator command received:
Actuator: fan
Action: ON
Reason: High temperature detected
Simulated Fan: ON
```

A dehumidifier command should display:

```text
Actuator command received:
Actuator: dehumidifier
Action: ON
Reason: High humidity detected
Simulated Dehumidifier: ON
```

A light command should display:

```text
Actuator command received:
Actuator: light
Action: ON
Reason: Light detected
Simulated Light: ON
```

This confirms that the actuator command was successfully published by the control component, passed through MQTT and received by the actuator simulator.

---

# Running the Complete Sensor-to-Actuator Pipeline

The complete pipeline requires three Python components to run at the same time.

Mosquitto must also be running.

Use three separate PowerShell or VS Code terminals.

Start the components in the following order.

## Step 1 - Start the Actuator Simulator

In the first terminal, from the root of the project run:

```powershell
py Prototype/Actuator_Simulator.py
```

Look for:

```text
Starting IoT actuator simulator...
Connected to MQTT broker: localhost:1883
Subscribed to MQTT topic: actuators/commands
Waiting for actuator commands...
```

Leave this terminal running.

---

## Step 2 - Start the Control Logic

In the second terminal run:

```powershell
py Prototype/Control_Logic.py
```

Look for:

```text
Starting IoT control logic...
Connected to MQTT broker: localhost:1883
Subscribed to MQTT topic: sensors/telemetry
Waiting for sensor readings...
```

Leave this terminal running.

---

## Step 3 - Start the Sensor Simulator

In the third terminal run:

```powershell
py Prototype/Data_Sensor.py
```

Look for:

```text
Connected to MQTT broker: localhost:1883
Starting IoT sensor simulation...
```

The sensor simulator should begin publishing readings to:

```text
sensors/telemetry
```

---

# What to Look For During the End-to-End Test

The three terminals demonstrate the different stages of the IoT pipeline.

## Sensor Terminal

The sensor terminal should display:

```text
Published to MQTT topic: sensors/telemetry
```

followed by the JSON sensor reading.

This confirms:

```text
CSV Dataset
    ↓
Data_Sensor.py
    ↓
MQTT
```

---

## Control Terminal

The control terminal should display:

```text
Sensor reading received:
```

followed by the JSON sensor data.

The terminal should then display either:

```text
Control decision: No action required
```

or one or more triggered control decisions.

For example:

```text
Control decisions:
- FAN ON - High temperature detected
Published actuator command to: actuators/commands
```

This confirms:

```text
MQTT Sensor Data
      ↓
Control_Logic.py
      ↓
Control Rules
      ↓
MQTT Actuator Command
```

---

## Actuator Terminal

When an actuator command is generated, the actuator terminal should display:

```text
Actuator command received:
```

followed by the actuator information.

For example:

```text
Actuator: fan
Action: ON
Reason: High temperature detected
Simulated Fan: ON
```

This confirms:

```text
MQTT Actuator Command
        ↓
Actuator_Simulator.py
        ↓
Simulated Action
```

---

# Complete Data Flow

When all three components are working correctly, the complete prototype flow is:

```text
IoT Telemetry CSV Dataset
          ↓
     Data_Sensor.py
          ↓
   JSON Sensor Reading
          ↓
 MQTT: sensors/telemetry
          ↓
 Eclipse Mosquitto
          ↓
    Control_Logic.py
          ↓
      Control Rules
          ↓
 JSON Actuator Command
          ↓
MQTT: actuators/commands
          ↓
 Eclipse Mosquitto
          ↓
 Actuator_Simulator.py
          ↓
 Simulated Fan / Dehumidifier / Light
```

---

# Control and Actuator Troubleshooting

## Control Logic Waiting for Sensor Readings

If `Control_Logic.py` displays:

```text
Waiting for sensor readings...
```

but nothing else appears, make sure `Data_Sensor.py` is running.

The sensor simulator must publish messages to:

```text
sensors/telemetry
```

The control component will remain waiting until a sensor message is received.

---

## Actuator Simulator Waiting for Commands

If `Actuator_Simulator.py` displays:

```text
Waiting for actuator commands...
```

this does not necessarily indicate an error.

The actuator simulator only receives a message when one of the configured control rules is triggered.

For example:

```text
Temperature >= 25°C
Humidity >= 70%
Light = True
```

If the sensor reading does not meet any of these conditions, no actuator command will be published.

---

## No Action Required

If the control terminal displays:

```text
Control decision: No action required
```

the system is working correctly.

This means the sensor message was successfully received but none of the configured control thresholds were reached.

---

## MQTT Connection Refused

If either Python component cannot connect to:

```text
localhost:1883
```

check that Eclipse Mosquitto is running.

The MQTT broker must be available before starting the sensor, control or actuator components.

---

## KeyboardInterrupt When Stopping

`Control_Logic.py` and `Actuator_Simulator.py` continuously listen for MQTT messages.

They can be stopped manually using:

```text
Ctrl+C
```

A `KeyboardInterrupt` message may appear when the program is stopped manually.

This is caused by manually terminating the continuously running MQTT listener and does not indicate that the MQTT processing failed.

---

# Control and Actuator Prototype Status

The control and actuator implementation has been successfully tested with:

- MQTT sensor subscription
- JSON sensor message decoding
- Temperature control rules
- Humidity control rules
- Light control rules
- JSON actuator command generation
- MQTT actuator command publishing
- MQTT actuator command subscription
- Fan simulation
- Dehumidifier simulation
- Light simulation
- End-to-end sensor-to-actuator testing

The completed prototype demonstrates:

```text
Sensor Dataset
      ↓
Sensor Simulator
      ↓
MQTT
      ↓
Control Logic
      ↓
MQTT
      ↓
Actuator Simulator
```

This demonstrates a working IoT control pipeline where simulated sensor data can automatically generate and execute simulated actuator actions.

---
# Grafana Visualisation

## Overview

Grafana is used to visualise the IoT sensor data stored in the project PostgreSQL database.

The current local data flow is:

```text
IoT Telemetry Dataset
        ↓
PostgreSQL Database
        ↓
Grafana PostgreSQL Datasource
        ↓
Grafana Dashboard
        ↓
Sensor Visualisation Panels

The sensor data is stored in the iot_telemetry_data table in PostgreSQL.

The table contains the following sensor fields:

ts - Timestamp
device - Device name
co - Carbon monoxide reading
humidity - Humidity reading
light - Light status
lpg - LPG reading
motion - Motion status
smoke - Smoke reading
temp - Temperature reading

The dataset contains approximately 405,000 sensor readings.

Grafana Setup

Grafana is running locally using Docker.

The Grafana container is available on:

http://localhost:3000

The PostgreSQL database is running locally on port 5432.

Grafana connects to PostgreSQL using the following settings:

Host: host.docker.internal:5432
Database: postgres
User: postgres
SSL Mode: disable

The PostgreSQL password is not stored in this documentation.

Grafana PostgreSQL Datasource

A PostgreSQL datasource was added in Grafana to connect to the project database.

The connection was tested successfully using Grafana's Save & Test option.

The datasource was then used in Grafana Explore to confirm that real sensor data could be retrieved from the iot_telemetry_data table.

Example query:

SELECT
    to_timestamp(ts) AS "time",
    temp
FROM iot_telemetry_data
ORDER BY ts
LIMIT 100;
Dashboard

A Grafana dashboard called:

IoT Sensor Data - Real Project

was created using the project sensor data.

The dashboard contains the following visualisation panels:

Humidity Readings
Temperature Readings
CO Readings
LPG Readings
Smoke Readings
Motion Readings
Light Readings

The dashboard was tested using the real data stored in PostgreSQL.

Sensor Queries

The panels use the ts field as the time value and the relevant sensor field for the reading.

Example temperature query:

SELECT
    to_timestamp(ts) AS "time",
    temp
FROM iot_telemetry_data
ORDER BY ts
LIMIT 100;

Example humidity query:

SELECT
    to_timestamp(ts) AS "time",
    humidity
FROM iot_telemetry_data
ORDER BY ts
LIMIT 100;

Example CO query:

SELECT
    to_timestamp(ts) AS "time",
    co
FROM iot_telemetry_data
ORDER BY ts
LIMIT 100;

Example LPG query:

SELECT
    to_timestamp(ts) AS "time",
    lpg
FROM iot_telemetry_data
ORDER BY ts
LIMIT 100;

Example smoke query:

SELECT
    to_timestamp(ts) AS "time",
    smoke
FROM iot_telemetry_data
ORDER BY ts
LIMIT 100;

For the boolean sensor values, the same approach is used with the motion and light fields.

Example motion query:

SELECT
    to_timestamp(ts) AS "time",
    motion
FROM iot_telemetry_data
ORDER BY ts
LIMIT 100;

Example light query:

SELECT
    to_timestamp(ts) AS "time",
    light
FROM iot_telemetry_data
ORDER BY ts
LIMIT 100;
Testing

The Grafana datasource was tested successfully against the local PostgreSQL database.

The dashboard was also tested with the project sensor dataset and confirmed to display real values for:

Temperature
Humidity
CO
LPG
Smoke
Motion
Light

The final dashboard was saved after removing duplicate panels.

Reproducing the Grafana Setup

To reproduce the Grafana setup on another machine:

Install Docker Desktop.
Make sure PostgreSQL is running.
Set up the project PostgreSQL database and import the sensor dataset.
Start Grafana using Docker.
Open Grafana at http://localhost:3000.
Add a PostgreSQL datasource using the local PostgreSQL connection details.
Test the datasource connection.
Create a dashboard using the iot_telemetry_data table.
Add panels for the required sensor readings.
Save the dashboard.