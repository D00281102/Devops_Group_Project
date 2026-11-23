import psycopg
import json
from kafka import KafkaConsumer, KafkaProducer
import paho.mqtt.client as mqtt
from api.db import get_connection, pool
from api.control_db import get_control_connection
import os

# MQTT configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
SENSOR_TOPIC = "sensors/telemetry"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9093")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sensor-telemetry")
KAFKA_GROUP_ID = "control-logic-consumer"
KAFKA_COMMAND_TOPIC = os.getenv("KAFKA_COMMAND_TOPIC", "actuator-commands")



def get_building_id(device_id):
    """
    Find which building a sensor device belongs to.
    """
    if not device_id:
        return None

    with get_control_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT building_id
                FROM building_devices
                WHERE device_id = %s
                """,
                (device_id,)
            )
            row = cur.fetchone()

    # Return None if the device isn't registered.
    if row is None:
        return None

    return row[0]



def get_control_settings(building_id=None):
    """
    Retrieve control settings for a specific building from PostgreSQL.
    """
    with get_control_connection() as conn:
        with conn.cursor() as cur:
            if building_id is None:
                # Use the original single-building settings.
                cur.execute(
                    """
                    SELECT temperature_threshold, humidity_threshold, light_enabled
                    FROM control_settings
                    WHERE id = 1
                    """
                )
            else:
                # Get settings for the selected building.
                cur.execute(
                    """
                    SELECT temperature_threshold, humidity_threshold, light_enabled
                    FROM control_settings
                    WHERE building_id = %s
                    """,
                    (building_id,)
                )

            row = cur.fetchone()


    if row is None:
        # Don't control a building without saved settings.
        if building_id is not None:
            return None

        # Keep the original single-building defaults.
        return {
            "temperature_threshold": 25,
            "humidity_threshold": 70,
            "light_enabled": True
        }


    return {
        "temperature_threshold": row[0],
        "humidity_threshold": row[1],
        "light_enabled": row[2]
    }


def get_latest_sensor_data():
    """
    Retrieve the latest sensor reading from the PostgreSQL database.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT records, ts, device, co, humidity, light,
                       lpg, motion, smoke, temp
                FROM iot_telemetry_data
                ORDER BY records DESC
                LIMIT 1
                """
            )

            row = cur.fetchone()

    if row is None:
        return None

    return {
        "records": row[0],
        "ts": row[1],
        "device": row[2],
        "co": row[3],
        "humidity": row[4],
        "light": row[5],
        "lpg": row[6],
        "motion": row[7],
        "smoke": row[8],
        "temp": row[9]
    }

def process_database_data(client):
    """
    Retrieve the latest sensor reading from the database,
    evaluate it and publish any required actuator commands.
    """
    sensor_data = get_latest_sensor_data()

    if sensor_data is None:
        print("No sensor data found in database.")
        return

    print("Latest database sensor reading:")
    print(json.dumps(sensor_data, indent=4))


    # Find which building this sensor belongs to.
    building_id = get_building_id(sensor_data.get("device"))

    if building_id is None:
        print("Unknown sensor device. Skipping control decisions.")
        return

    # Use the settings for this building.
    settings = get_control_settings(building_id)

    if settings is None:
        print(f"No control settings found for Building {building_id}. Skipping.")
        return

    commands = evaluate_sensor_data(sensor_data, settings)

    if commands:
        print("Control decisions:")

        for command in commands:
            print(
                f"- {command['actuator'].upper()} "
                f"{command['action']} - {command['reason']}"
            )

            publish_actuator_command(client, command, building_id)
    else:
        print("Control decision: No action required")

def get_control_settings():
    """
    Retrieve the saved control settings from PostgreSQL.
    """
    with get_control_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT temperature_threshold, humidity_threshold, light_enabled
                FROM control_settings
                WHERE id = 1
                """
            )
            row = cur.fetchone()

    if row is None:
        return {
            "temperature_threshold": 25,
            "humidity_threshold": 70,
            "light_enabled": True
        }

    return {
        "temperature_threshold": row[0],
        "humidity_threshold": row[1],
        "light_enabled": row[2]
    }

def get_latest_sensor_data():
    """
    Retrieve the latest sensor reading from the PostgreSQL database.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT records, ts, device, co, humidity, light,
                       lpg, motion, smoke, temp
                FROM iot_telemetry_data
                ORDER BY records DESC
                LIMIT 1
                """
            )

            row = cur.fetchone()

    if row is None:
        return None

    return {
        "records": row[0],
        "ts": row[1],
        "device": row[2],
        "co": row[3],
        "humidity": row[4],
        "light": row[5],
        "lpg": row[6],
        "motion": row[7],
        "smoke": row[8],
        "temp": row[9]
    }

def process_database_data(client):
    """
    Retrieve the latest sensor reading from the database,
    evaluate it and publish any required actuator commands.
    """
    sensor_data = get_latest_sensor_data()

    if sensor_data is None:
        print("No sensor data found in database.")
        return

    print("Latest database sensor reading:")
    print(json.dumps(sensor_data, indent=4))

    settings = get_control_settings()
    commands = evaluate_sensor_data(sensor_data, settings)

    if commands:
        print("Control decisions:")

        for command in commands:
            print(
                f"- {command['actuator'].upper()} "
                f"{command['action']} - {command['reason']}"
            )

            publish_actuator_command(client, command)
    else:
        print("Control decision: No action required")

def on_connect(client, userdata, flags, reason_code, properties):
    """
    Connect to MQTT and subscribe to live sensor readings.
    """
    if reason_code == 0:
        print(f"Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"Actuator commands will be published to: {ACTUATOR_TOPIC}")

        client.subscribe(SENSOR_TOPIC)
        print(f"Subscribed to MQTT topic: {SENSOR_TOPIC}")
    else:
        print(f"MQTT connection failed: {reason_code}")

def evaluate_sensor_data(sensor_data, settings=None):
    """
    Evaluate sensor readings using configurable control settings.
    """
    if settings is None:
        settings = {
            "temperature_threshold": 25,
            "humidity_threshold": 70,
            "light_enabled": True
        }

    commands = []

    if sensor_data["temp"] >= settings["temperature_threshold"]:
        commands.append({
            "actuator": "fan",
            "action": "ON",
            "reason": "High temperature detected"
        })

    if sensor_data["humidity"] >= settings["humidity_threshold"]:
        commands.append({
            "actuator": "dehumidifier",
            "action": "ON",
            "reason": "High humidity detected"
        })

    if settings["light_enabled"] and sensor_data["light"]:
        commands.append({
            "actuator": "light",
            "action": "ON",
            "reason": "Light detected"
        })

    return commands

_command_producer = None


def get_command_producer():
    """
    Reuse one Kafka producer for actuator commands.
    """
    global _command_producer

    if _command_producer is None:
        _command_producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value).encode("utf-8")
        )

    return _command_producer


def publish_actuator_command(client, command, building_id):
    """
    Publish a building-specific actuator command to Kafka.
    """
    payload_data = {**command, "building_id": building_id}

    producer = get_command_producer()
    producer.send(
        KAFKA_COMMAND_TOPIC,
        key=str(building_id).encode("utf-8"),
        value=payload_data
    ).get(timeout=10)

    print(f"Published actuator command to Kafka: {KAFKA_COMMAND_TOPIC}")
    print(json.dumps(payload_data, indent=4))


def on_message(client, userdata, message):
    """
    Receive sensor data, evaluate it and publish actuator commands.
    """
    try:
        sensor_data = json.loads(message.payload.decode("utf-8"))

        print("Sensor reading received:")
        print(json.dumps(sensor_data, indent=4))

        settings = get_control_settings()
        commands = evaluate_sensor_data(sensor_data, settings)

        if commands:
            print("Control decisions:")

            for command in commands:
                print(
                    f"- {command['actuator'].upper()} "
                    f"{command['action']} - {command['reason']}"
                )

                publish_actuator_command(client, command, building_id)

        else:
            print("Control decision: No action required")

        print()

    except json.JSONDecodeError:
            print("Error: Received message is not valid JSON.")

def start_control_logic():
    """
    Connect to MQTT, process the latest database reading,
    and continuously listen for live sensor readings.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.on_connect = on_connect
    client.on_message = on_message

    print("Starting IoT control logic...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    try:
        client.loop_start()

        print("Retrieving latest sensor reading from database...\n")
        process_database_data(client)

        print(f"Listening for live sensor readings on: {SENSOR_TOPIC}")

        # Keep the control logic running to receive MQTT messages.
        while True:
            import time
            time.sleep(1)

    except KeyboardInterrupt:
        print("Stopping IoT control logic...")

    finally:
        client.loop_stop()
        client.disconnect()
        if _command_producer is not None:
            _command_producer.flush()
            _command_producer.close()
        pool.close()

        # Historical telemetry lookup is optional for Kafka mode.
        if os.getenv('PROCESS_HISTORICAL_TELEMETRY', 'false').lower() == 'true':
            process_database_data(client)

        print(f"Listening for live sensor readings on: {SENSOR_TOPIC}")

        # Keep the control logic running to receive MQTT messages.
        start_kafka_consumer(client)
        while True:
            import time
            time.sleep(1)


def start_kafka_consumer(client):
    """
    Consume Kafka telemetry using the existing control logic.
    """
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="latest",
        enable_auto_commit=True
    )

    print(f"Listening for Kafka telemetry on: {KAFKA_TOPIC}")

    try:
        for message in consumer:
            class SensorMessage:
                payload = message.value

            on_message(client, None, SensorMessage())

    finally:
        consumer.close()

if __name__ == "__main__":
    start_control_logic()

