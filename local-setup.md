# DevOps Group Project — Local Setup and Developer Reference

> **Purpose:** Local Windows/Python development, manual MQTT/Kafka, sensor and actuator testing, Grafana, and telemetry/control API reference. Docker Compose deployment, authentication and multi-building evidence are in [`containerized-setup.md`](containerized-setup.md).
>
> **Version note:** The source documents span multiple stages of development. Historical instructions and test results are preserved, but they are not guarantees about the current branch. Never commit `.env` files, credentials or JWT signing secrets.

## Quick navigation

- Sensor simulator, dataset and Mosquitto: sections below
- Manual Kafka and Kafka Connect: **Kafka Integration**
- Local control logic and actuator simulator: **MQTT Control Logic and Actuator Simulator**
- Grafana and its real-data dashboard: **Grafana Visualisation**
- Telemetry API, endpoints and local PostgreSQL: **IoT Telemetry API**
- Original Grafana tests and legacy control API: historical sections at the end

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

│   ├── data/

│   │   └── iot_telemetry_data.csv

│   │

│   ├── Data_Sensor.py

│   ├── Control_Logic.py

│   ├── Actuator_Simulator.py

│   └── requirements.txt

├── .gitignore

└── local-setup.md

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

C:\Program Files\mosquitto\\

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

```te[Confluent Platform](https://www\.confluent.io/hub/confluentinc/kafka-connect-mqtt)

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

          "mqtt.server.uri" = "tcp\://localhost:1883"

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

Temperature >= 25°C  → Fan ON

Humidity >= 70%      → Dehumidifier ON

Light = True         → Light ON

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

## Grafana Visualisation
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
```

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

## Grafana Setup

Grafana is running locally using Docker.

The Grafana container is available on:

http://localhost:3001

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

## Sensor Queries

The panels use the ts field as the time value and the relevant sensor field for the reading.

## Example temperature query:

```sql

SELECT

    to_timestamp(ts) AS "time",

    temp

FROM iot_telemetry_data

ORDER BY ts

LIMIT 100;

```

## Example humidity query:
```sql

SELECT

    to_timestamp(ts) AS "time",

    humidity

FROM iot_telemetry_data

ORDER BY ts

LIMIT 100;

```

## Example CO query:
```sql

SELECT

    to_timestamp(ts) AS "time",

    co

FROM iot_telemetry_data

ORDER BY ts

LIMIT 100;

```

## Example LPG query:
```sql

SELECT

    to_timestamp(ts) AS "time",

    lpg

FROM iot_telemetry_data

ORDER BY ts

LIMIT 100;

```

## Example smoke query:
```sql

SELECT

    to_timestamp(ts) AS "time",

    smoke

FROM iot_telemetry_data

ORDER BY ts

LIMIT 100;

```

For the boolean sensor values, the same approach is used with the motion and light fields.

## Example motion query:
```sql

SELECT

    to_timestamp(ts) AS "time",

    motion

FROM iot_telemetry_data

ORDER BY ts

LIMIT 100;

```

## Example light query:
```sql

SELECT

    to_timestamp(ts) AS "time",

    light

FROM iot_telemetry_data

ORDER BY ts

LIMIT 100;

```

## Testing
The datasource and dashboard are configured using the files in `Prototype/grafana/provisioning` and `Prototype/grafana/dashboards`. Grafana uses the `grafana-data` Docker volume to preserve its data when the container is recreated.

The Grafana datasource was tested successfully against the local PostgreSQL database.

The dashboard contains the following visualisation panels:

- Humidity Readings

- Temperature Readings

- CO Readings

- LPG Readings

- Smoke Readings

- Current Motion Status

- Current Light Status

- Current Temperature

The final dashboard was saved after removing duplicate panels.

## Reproducing the Grafana Setup
To reproduce the Grafana setup on another machine:

- Install Docker Desktop and make sure it is running.

- Make sure PostgreSQL is running locally and that the project database and sensor dataset have been imported.

- In the project root directory, copy .env.example to .env.

- Open .env and set GF_DATASOURCE_PASSWORD to the password for the local PostgreSQL user. Do not commit or share this file.

- Open PowerShell in the project root directory.

- Validate the Docker Compose configuration:

  ```powershell

  docker compose config --quiet

  ```

- Start Grafana:

  ```powershell

  docker compose up -d grafana

  ```

- Open Grafana at http://localhost:3001.

- Check that the PostgreSQL datasource connects successfully and that the IoT Sensor Data - Real Project dashboard loads.

- Confirm that the dashboard panels display sensor data.

The datasource and dashboard are configured using the files in Prototype/grafana/provisioning and Prototype/grafana/dashboards. Grafana uses the grafana-data Docker volume to preserve its data when the container is recreated.

The .env file contains local credentials and must not be committed to Git.

---

## Control Logic Docker Container Setup
### Overview
The IoT Control Logic service has been containerized using Docker.

The container runs Control_Logic.py, which connects to the

MQTT broker, retrieves sensor data from PostgreSQL and

evaluates whether actuator commands are required.

### Prerequisites
Before running the Control Logic container, ensure:

- Docker Desktop is installed and running.

- PostgreSQL is running locally on port 5434.

- The IoT telemetry database has been set up.

- Mosquitto MQTT broker is running on port 1883.

- Prototype/.env contains the required database credentials.

### Docker Configuration
The Dockerfile is located at:

Prototype/Dockerfile.control

The Control Logic service is configured in the root

docker-compose.yml file.

The container uses host.docker.internal to communicate

with PostgreSQL and MQTT running on the host machine.

### Environment Variables
| Variable | Description |

| --- | --- |

| MQTT_BROKER | MQTT broker hostname |

| MQTT_PORT | MQTT broker port |

| DB_HOST | PostgreSQL hostname |

| DB_PORT | PostgreSQL port |

| DB_NAME | Database name |

| DB_USER | Database username |

| DB_PASSWORD | Database password |

The database password is loaded from Prototype/.env.

This file must not be committed to Git.

### Building and Running the Control Logic Container
Open PowerShell in the project root directory.

Make sure Docker Desktop, PostgreSQL and the Mosquitto MQTT broker are running.

**1. Validate the Docker Compose configuration:**

```powershell

docker compose --env-file ./Prototype/.env config --quiet

```

**2. Build the Control Logic Docker image:**

```powershell

docker compose --env-file ./Prototype/.env build control-logic

```

**3. Run the Control Logic container:**

```powershell

docker compose --env-file ./Prototype/.env run --rm --no-deps control-logic

```

The container connects to the MQTT broker and PostgreSQL database.

It retrieves the latest sensor reading, evaluates the control rules and publishes actuator commands when required.

The current startup process checks the latest database reading and then exits. It does not continuously listen for incoming MQTT sensor readings.

### Running the Actuator Simulator
Open a separate PowerShell terminal and run:

```powershell

python .\Prototype\Actuator_Simulator.py

```

The Actuator Simulator subscribes to the `actuators/commands` MQTT topic and waits for commands.

### Testing and Verification
The Control Logic container was tested successfully using Docker Compose.

The following tests were completed:

- Docker image built successfully.

- Container connected to the MQTT broker on port 1883.

- Container connected to PostgreSQL on port 5434.

- Latest sensor reading retrieved successfully from PostgreSQL.

- Control rules evaluated successfully.

- Actuator Simulator received MQTT commands.

**Control Logic Integration Test**

A simulated temperature reading of 30°C was passed to the Control Logic functions running inside Docker.

The Control Logic correctly detected the high temperature and published a fan ON command to the `actuators/commands` MQTT topic.

The Actuator Simulator received the command and displayed:

```text

Actuator command received:

Actuator: fan

Action: ON

Reason: High temperature detected

Simulated Fan: ON

```

This confirmed successful communication between the Dockerized Control Logic, MQTT broker and Actuator Simulator.

The simulated reading was used for testing without modifying the PostgreSQL database.

### Troubleshooting
- **Docker not responding:** Check that Docker Desktop is running and its engine has started.

- **MQTT connection failed:** Check that Mosquitto is running on port 1883.

- **PostgreSQL connection failed:** Check port 5434 and the database credentials in `Prototype/.env`.

- **Code changes not appearing:** Rebuild the Control Logic Docker image.

- **Grafana password warning:** Configure `GF_DATASOURCE_PASSWORD` if required for the Grafana setup.

### Current Limitations
The current Control Logic startup retrieves and evaluates the latest PostgreSQL sensor reading, then exits.

Continuous MQTT sensor subscriptions are not enabled in the current startup function. This requires further integration work.

## Sensor and Actuator Simulator Docker Setup
The Sensor Simulator and Actuator Simulator have been containerized using Docker.

Both services connect to the local Mosquitto MQTT broker using `host.docker.internal:1883`.

### Prerequisites
- Docker Desktop running

- Mosquitto MQTT broker running on port 1883

- `Prototype/.env` configured

### Build the containers
```powershell

docker compose --env-file ./Prototype/.env build sensor-simulator actuator-simulator

```

### Run the Sensor Simulator
```powershell

docker compose --env-file ./Prototype/.env run --rm --no-deps sensor-simulator

```

The Sensor Simulator reads the IoT telemetry CSV dataset and publishes 10 JSON readings to the `sensors/telemetry` MQTT topic.

### Run the Actuator Simulator
```powershell

docker compose --env-file ./Prototype/.env run --rm --no-deps actuator-simulator

```

The Actuator Simulator subscribes to `actuators/commands` and continuously listens for commands from the Control Logic.

### Testing
Both containers were built and tested successfully.

- Sensor Simulator connected to MQTT and published 10 readings.

- Actuator Simulator connected to MQTT and subscribed to `actuators/commands`.

- A test command was published to MQTT.

- Actuator Simulator received the command and simulated switching the fan ON.

The complete sensor-to-control-to-actuator pipeline still requires integration testing.

---

# Telemetry HTTP API — additional reference from the original README

The following section consolidates the original root README. It documents the telemetry CRUD API, PostgreSQL schema, setup, network options, error handling and development practices. Some paths, versions, branches and environment values describe the original development setup; verify them against the checked-out code and current deployment before use. Do not expose PostgreSQL directly to the public internet.

## IoT Telemetry API — original README reference
HTTP API that exposes the `iot_telemetry_data` table in PostgreSQL so the

front-end interface can read and modify telemetry records.

Built with FastAPI, psycopg 3, and Pydantic.

Each developer runs their own copy of the stack. The API and Postgres do

not need to be on the same network as the rest of the team. See section

9.4 if you're not on the same LAN as whoever is hosting the database.

\> Troubleshooting errors encountered during development are documented

\> separately in Jira under the API workstream. If something breaks, check

\> there first before pinging the team.

---

## 1. What this API does
It sits between the PostgreSQL database and the front-end interface.

    Front-end  ->  API (this folder)  ->  PostgreSQL

    (teammate)     (you, now)             (iot_telemetry_data table)

The front-end calls HTTP endpoints. This API translates those calls into SQL

and returns JSON.

Five endpoints:

| Method | Path                    | Purpose                                |

|--------|-------------------------|----------------------------------------|

| GET    | /telemetry              | List rows (query: limit, offset)       |

| GET    | /telemetry/{record_id}  | Fetch one row by records id            |

| POST   | /telemetry              | Insert a new row                       |

| PUT    | /telemetry/{record_id}  | Update specific fields on a row        |

| DELETE | /telemetry/{record_id}  | Delete a row                           |

---

## 2. Project layout
    Prototype/

    ├── .env                    <- DB credentials (gitignored, NOT committed)

    ├── .gitignore              <- ignores .env

    ├── requirements.txt        <- Python dependencies

    ├── Data_Sensor.py          <- MQTT publisher (separate workstream)

    └── api/

        ├── __init__.py

        ├── config.py           <- reads .env, builds DATABASE_URL

        ├── db.py               <- connection pool, get_connection()

        ├── models.py           <- Pydantic schemas (shape of a row)

        ├── routes.py           <- the five HTTP endpoints

        ├── errors.py           <- JSON error handlers for DB failures

        └── main.py             <- FastAPI app entry point

---

## 3. Setup — for teammates cloning the repo
### 3.1 Install Python 3.12 or newer
Python 3.11 will NOT work. The uvicorn version pulled in by the current

requirements file imports `typing.NotRequired`, which only exists from

Python 3.12 onward.

Install Python 3.13 (matches the machines we tested on):

    winget install --id Python.Python.3.13

Close every PowerShell/VS Code window afterwards and open a new one. Then:

    python --version      # should print Python 3.13.x

### 3.2 Clone the repo
    git clone https://github.com/D00281102/Devops_Group_Project.git

Then switch to your branch:

    git checkout Jo          # or Bright / Daniils / Simon — use your own

Branch names are case-sensitive.

### 3.3 Install the packages
From the repo root:

    pip install -r Prototype/requirements.txt

Or manually:

    pip install fastapi uvicorn "psycopg[binary]" python-dotenv psycopg_pool

### 3.4 Create your own `.env`
`.env` is gitignored on purpose — every machine has its own copy with its own

DB values. Create `Prototype/.env` with:

    DB_HOST=localhost

    DB_PORT=5434

    DB_NAME=postgres

    DB_USER=postgres

    DB_PASSWORD=\<your postgres password>

Notes:

- `DB_HOST=localhost` if Postgres is on the same machine.

- `DB_HOST=192.168.1.6` if Postgres is on the other laptop on the network.

- `DB_NAME` must be the database that actually contains the

  `iot_telemetry_data` table. On our setup that's `postgres`.

### 3.5 Check Postgres is reachable
    psql -U postgres -h localhost -p 5434 -l

Should list databases. If `psql` isn't on PATH:

    & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -p 5434 -l

Verify the table exists:

    psql -U postgres -h localhost -p 5434 -d postgres -c "\dt"

You should see `iot_telemetry_data` in the list.

If the table isn't there and you're on your own machine, see section 9.4

Option A for how to create it and load the CSV.

---

## 4. Running the API
From the `Prototype` folder:

    python -m uvicorn api.main:app --reload

You must be in `Prototype`, not the repo root — the import path

`api.main:app` resolves relative to the current directory.

You should see:

    INFO:     Uvicorn running on http://127.0.0.1:8000

    INFO:     Application startup complete.

No traceback, no "pool" errors = good.

### 4.1 Interactive API docs (free, auto-generated)
Open in a browser:

    http://127.0.0.1:8000/docs      <- Swagger UI (test requests here)

    http://127.0.0.1:8000/redoc     <- ReDoc (nice to read)

Use Swagger for testing. Click any endpoint, click **Try it out**, paste a

body, click **Execute**. It handles JSON formatting for you — do NOT try to

run the bash-style curl command that Swagger shows at the bottom.

---

## 5. Testing the endpoints
### Health check
    curl.exe http://127.0.0.1:8000/

Should return `{"status":"ok"}`.

### List rows
    curl.exe "http://127.0.0.1:8000/telemetry?limit=3"

Returns an array of row objects.

### Fetch one row
    curl.exe "http://127.0.0.1:8000/telemetry/1"

Returns a single object.

### POST / PUT / DELETE
Use the Swagger page at `/docs` — PowerShell mangles the quotes in a curl

JSON body. Or use `curl.exe` with a JSON file:

    curl.exe -X POST "http://127.0.0.1:8000/telemetry" ^

      -H "Content-Type: application/json" ^

      --data-binary "@body.json"

where `body.json` contains the JSON payload.

---

## 6. Configuration reference
Read from `Prototype/.env` by `api/config.py`:

| Variable    | Default     | Meaning                                       |

|-------------|-------------|-----------------------------------------------|

| DB_HOST     | localhost   | Postgres hostname or IP                       |

| DB_PORT     | 5434        | Postgres port                                 |

| DB_NAME     | postgres    | Database containing iot_telemetry_data        |

| DB_USER     | postgres    | Postgres user                                 |

| DB_PASSWORD | ""          | Postgres password (required)                  |

These are combined into a `DATABASE_URL` of the form:

    postgresql://USER:PASSWORD\@HOST:PORT/DB_NAME

which the connection pool in `api/db.py` uses.

---

## 7. Error responses
All errors return JSON in the shape:

    {"detail": "...", "error": "..."}   (for DB errors)

    {"detail": "..."}                    (for validation / not-found)

| Status | When it happens                                     |

|--------|-----------------------------------------------------|

| 400    | PUT with an empty body (no fields to update)        |

| 404    | record_id doesn't exist in the table                |

| 409    | DB constraint violated (e.g. NOT NULL, wrong type)  |

| 422    | Request body failed validation (FastAPI auto)       |

| 503    | Database unreachable (pool couldn't connect)        |

The 422 responses come from FastAPI/Pydantic automatically — you don't need

to raise them yourself. The 503 and 409 come from `api/errors.py`.

---

## 8. Architecture notes — why it's built this way
### Connection pool, not one connection per request
`api/db.py` creates a single `ConnectionPool` at import time. Every request

borrows a connection and returns it when done. This avoids the cost of

opening a fresh TCP+auth connection for every request. Standard pattern for

web servers.

### Three separate Pydantic models
- `TelemetryRow` — what the API returns (includes `records`).

- `TelemetryCreate` — what the client sends for POST (no `records`; the DB

  generates it).

- `TelemetryUpdate` — all fields optional, defaults to `None`. Used with

  `model_dump(exclude_unset=True)` so PUT only updates the fields the client

  actually sent. Sending `{"temp": 25}` leaves everything else alone.

### `conn.commit()` is required
psycopg does not auto-commit. Any INSERT/UPDATE/DELETE must call

`conn.commit()` inside the connection block, or the change rolls back when

the connection returns to the pool.

### Parameterised SQL only
Every query uses `%s` placeholders and passes values as a tuple. The one

exception is the PUT route, which builds `SET col = %s, ...` from the keys

of a Pydantic model — those keys come from our code, not user input, so

they're safe. The values are still parameterised.

---

## 9. Network setup — if Postgres is on another machine
This section only applies if you're trying to reach the team's Postgres

over a network. If you're running your own Postgres locally, go straight to

section 9.4 Option A and ignore 9.1–9.3.

If the API runs on machine A and Postgres runs on machine B, three things

must be true on machine B (the Postgres machine):

### 9.1 `postgresql.conf` — allow external connections
`C:\Program Files\PostgreSQL\17\data\postgresql.conf`

Set:

    listen_addresses = '*'

(Remove the `#` at the start of the line.)

To check it's already listening externally:

    Get-NetTCPConnection -State Listen | Where-Object {$_.LocalPort -eq 5434}

If LocalAddress shows `0.0.0.0`, it's already accepting external connections.

### 9.2 `pg_hba.conf` — allow your network range
`C:\Program Files\PostgreSQL\17\data\pg_hba.conf`

Add as the **last line** of the file:

    host    all    all    192.168.1.0/24    scram-sha-256

Change `192.168.1.0/24` to match your network. Rules are matched top-down,

first match wins, so this line catches everything the localhost rules don't.

Edit with Notepad run as Administrator (right-click Notepad → Run as admin).

### 9.3 Windows Firewall — open the port
In an Administrator PowerShell on the Postgres machine:

    New-NetFirewallRule -DisplayName "Postgres 5434" -Direction Inbound -Protocol TCP -LocalPort 5434 -Action Allow

Restart Postgres afterwards:

    Restart-Service postgresql-x64-17

Then on machine A, set `DB_HOST=\<B's IP>` in `.env`.

### 9.4 If you are NOT on the same network as the Postgres machine
Everything in 9.1–9.3 only works when both machines are on the same LAN

(same Wi-Fi, same home network). If your machine is somewhere else —

different house, college network, mobile hotspot — the connection will time

out no matter how Postgres is configured.

**Before you read any further**: Option A below sets up a completely fresh,

independent stack on your own machine. If you take that route, everything

you already did in sections 3.1–3.3 still applies (Python, clone, packages).

Section 3.4 onwards changes, because you'll be pointing at your own

database, not the team's. Work through section 9.4 Option A and then come

back to section 4 to run the API.

You have three options. Pick the one that fits.

**Option A — Load the CSV into your own local Postgres (recommended)**

This is the cleanest option. You don't need anyone else's machine.

1. Install Postgres on your own machine (port 5434 to match the team setup,

   or whatever you want — you control it).

2. Get the CSV file. It's `iot_telemetry_data.csv` and should be in the

   repo, under `Prototype/data/`. If it's not there, ask the team.

3. Create the table. In psql:

       psql -U postgres -h localhost -p 5434 -d postgres

   Then paste:

       CREATE TABLE iot_telemetry_data (

           records  SERIAL PRIMARY KEY,

           ts       DOUBLE PRECISION NOT NULL,

           device   TEXT NOT NULL,

           co       DOUBLE PRECISION NOT NULL,

           humidity DOUBLE PRECISION NOT NULL,

           light    BOOLEAN NOT NULL,

           lpg      DOUBLE PRECISION NOT NULL,

           motion   BOOLEAN NOT NULL,

           smoke    DOUBLE PRECISION NOT NULL,

           temp     DOUBLE PRECISION NOT NULL

       );

   (If a teammate already has this table, run `\d iot_telemetry_data` on

   their machine to get the exact column types and match them. Mismatched

   types cause confusing errors later.)

4. Load the CSV. Easiest way is pgAdmin:

   - Open pgAdmin, connect to your local server.

   - Right-click `iot_telemetry_data` → **Import/Export Data**.

   - Mode: Import. Filename: point at the CSV. Format: csv. Header: Yes.

   - Columns: match the CSV's column order to the table's columns.

   - Click OK.

   Or from psql (faster if you're comfortable):

       \copy iot_telemetry_data (ts, device, co, humidity, light, lpg, motion, smoke, temp) FROM 'C:/path/to/iot_telemetry_data.csv' WITH (FORMAT csv, HEADER true);

   Note: `\copy` needs forward slashes even on Windows.

5. Set your `.env`:

       DB_HOST=localhost

       DB_PORT=5434

       DB_NAME=postgres

       DB_USER=postgres

       DB_PASSWORD=\<your own password>

6. **Now go back to section 4** and start the API as normal. Everything from

   section 4 onwards works exactly the same; it just talks to your own

   database instead of the team's.

You now have a fully independent dev environment. Nothing depends on anyone

else's machine.

**Option B — Run Postgres in Docker on your own machine**

If you have Docker, this skips the Postgres installer entirely:

    docker run --name iot-postgres -e POSTGRES_PASSWORD=yourpassword -p 5434:5432 -d postgres:17

Then load the CSV into it the same way as Option A steps 3–4. `.env` stays

as `DB_HOST=localhost`, `DB_PORT=5434`. Once your container is up, go back

to section 4 to run the API.

Your repo already has a `docker-compose.yml` — check whether it already

defines a Postgres service before starting a separate container.

**Option C — Tunnel to the Postgres machine**

Only worth doing if you specifically need to see the same data everyone

else sees, live. Tools like Tailscale or ngrok create a private network

between machines across the internet. This adds setup and security

considerations and isn't needed for development. Avoid unless you have a

specific reason.

**What NOT to do**

Do not try to expose Postgres directly to the public internet by

port-forwarding on your router. Postgres has no business being reachable

from the open internet, and you'll get scanned and attacked within hours.

If you need remote access, use a tunnel (Option C), never a port forward.

---

## 10. What the front-end teammate needs to know
- Base URL when running locally: `http://127.0.0.1:8000`

- All responses are JSON.

- Data shape: see `api/models.py`, or open `/docs` and look at the schemas.

- Field names are exactly as in the table: `records`, `ts`, `device`, `co`,

  `humidity`, `light`, `lpg`, `motion`, `smoke`, `temp`.

- `light` and `motion` are booleans. Everything else numeric is a float

  except `records` (integer) and `device` (string).

- Pagination on the list endpoint: `?limit=100&offset=0`. Defaults are

  100 and 0.

- Errors: always check the HTTP status code. 4xx = your request, 5xx =

  server/DB side. Body always has a `detail` field.

- For testing the API without writing client code, use

  `http://127.0.0.1:8000/docs`.

---

## 11. Git workflow
- Work on your own branch (`Jo`, `Bright`, `Daniils`, `Simon`, ...).

- Push to your branch: `git push origin \<branch>`.

- Do NOT push directly to `main` after this point.

- To merge your work into `main`: open a Pull Request on GitHub, get it

  reviewed, then merge.

- Never commit `.env`. It's gitignored — if `git status` shows it, something

  is wrong with `.gitignore`.

---

## 12. Quick reference
Start the server:

    cd Prototype

    python -m uvicorn api.main:app --reload

Test in browser:

    http://127.0.0.1:8000/docs

Test in terminal:

    curl.exe "http://127.0.0.1:8000/telemetry?limit=3"

Stop the server:

    Ctrl+C in the terminal running uvicorn

List databases:

    psql -U postgres -h localhost -p 5434 -l

List tables in `postgres`:

    psql -U postgres -h localhost -p 5434 -d postgres -c "\dt"

View all telemetry rows directly in SQL:

    psql -U postgres -h localhost -p 5434 -d postgres -c "SELECT * FROM iot_telemetry_data LIMIT 10;"

---

# Historical Grafana Investigation and Test Evidence

This section preserves the early Grafana investigation from the former `Grafana_README.md`. It describes historical tests, **not** the current provisioned dashboard. The current real-data Grafana instructions are in the Grafana Visualisation section above.

## Initial Grafana container and TestData dashboard

The initial image was `grafana/grafana:latest`, tested as Grafana 13.2.2, with container name `grafana` and host port 3000:

```powershell
docker run -d --name grafana -p 3000:3000 grafana/grafana:latest
docker start grafana
```

The initial dashboard `IoT Sensor Data - Grafana Test` used Grafana's built-in TestData datasource and a `Sensor Data Time Series` panel. This established that Grafana could create and display time-series visualisations before connecting the project database. TestData was synthetic, not actual IoT telemetry.

## Local PostgreSQL 17.11 test

A separate local PostgreSQL 17.11 server was tested on `localhost:5432`. `Get-Service *postgres*` showed the service running, and `Test-NetConnection localhost -Port 5432` returned `TcpTestSucceeded : True`. The historical test used the `postgres` database and a local-only test credential; no password is reproduced here. The Grafana datasource used `host.docker.internal:5432`, username `postgres`, SSL disabled and PostgreSQL version 17. Grafana's Save & test returned `Database Connection OK`.

The original test schema and data were:

```sql
CREATE TABLE dummy_sensor_data (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMP NOT NULL,
    device VARCHAR(50),
    temp DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    light DOUBLE PRECISION,
    co DOUBLE PRECISION,
    lpg DOUBLE PRECISION,
    motion BOOLEAN,
    smoke DOUBLE PRECISION
);

INSERT INTO dummy_sensor_data
(ts, device, temp, humidity, light, co, lpg, motion, smoke)
VALUES
('2026-09-29 14:00:00', 'sensor-01', 22.5, 48.2, 350, 0.4, 1.2, true, 0.1),
('2026-09-29 14:05:00', 'sensor-01', 23.1, 49.0, 370, 0.5, 1.3, false, 0.1),
('2026-09-29 14:10:00', 'sensor-01', 23.8, 50.1, 390, 0.5, 1.4, true, 0.2),
('2026-09-29 14:15:00', 'sensor-01', 24.2, 51.3, 410, 0.6, 1.5, false, 0.2),
('2026-09-29 14:20:00', 'sensor-01', 24.8, 52.0, 430, 0.7, 1.6, true, 0.3);

SELECT * FROM dummy_sensor_data ORDER BY ts;
SELECT ts AS "time", temp FROM dummy_sensor_data ORDER BY ts;
```

PostgreSQL returned `INSERT 0 5`. The query retrieved five rows and Grafana displayed temperatures rising from 22.5 to 24.8. The `IoT Sensor Data Dashboard` dashboard with `Temperature Readings` panel was saved, refreshed and verified to persist. This historical test database/table is separate from the current real-data `iot_telemetry_data` setup.

# Legacy Control Settings API (historical reference)

The original FastAPI Control Settings API used `http://127.0.0.1:8000`, with interactive Swagger documentation at `http://127.0.0.1:8000/docs`. From the repository root, its original development command was:

```powershell
python -m uvicorn api.main:app --app-dir Prototype --reload
```

The original endpoints were `GET /control-settings` (retrieve persisted settings) and `PUT /control-settings` (update them). Both returned HTTP 200 and the JSON structure:

```json
{
  "temperature_threshold": 30,
  "humidity_threshold": 75,
  "light_enabled": true
}
```

These values are examples, not defaults. The original defaults were 25 degrees Celsius, 70% humidity and `light_enabled: true`. The accepted temperature range was -50 to 100 degrees Celsius; humidity range 0 to 100%; invalid values returned 422. Settings persisted in PostgreSQL `control_settings`. **Important:** SCRUM-122's 2 November 2026 report states the legacy control-settings endpoints were disabled in SCRUM-121 and frontend migration was outstanding. Do not assume these endpoints are active in the current version.
