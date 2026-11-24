import json
import paho.mqtt.client as mqtt
from api.db import get_connection, pool

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
SENSOR_TOPIC = "sensors/telemetry"
ACTUATOR_TOPIC = "actuators/commands"

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

def get_control_settings():
    """
    Retrieve the latest control settings from PostgreSQL.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT temperature_threshold,
                       humidity_threshold,
                       light_enabled
                FROM control_settings
                WHERE id = 1
            """)

            row = cur.fetchone()

    if row is None:
        raise RuntimeError("Control settings not found in database.")

    return {
        "temperature_threshold": row[0],
        "humidity_threshold": row[1],
        "light_enabled": row[2]
    }


def on_connect(client, userdata, flags, reason_code, properties):
    """
    Subscribe to sensor readings after connecting to MQTT.
    """
    if reason_code == 0:
        print(f"Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"Subscribing to: {SENSOR_TOPIC}")

        client.subscribe(SENSOR_TOPIC)

        print(f"Actuator commands will be published to: {ACTUATOR_TOPIC}")
    else:
        print(f"MQTT connection failed: {reason_code}")


def evaluate_sensor_data(sensor_data, settings):
    """
    Evaluate sensor readings using the latest control settings.
    """
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


def publish_actuator_command(client, command):
    """
    Publish an actuator command to the MQTT broker.
    """
    payload = json.dumps(command)

    client.publish(
        ACTUATOR_TOPIC,
        payload
    )

    print(f"Published actuator command to: {ACTUATOR_TOPIC}")
    print(json.dumps(command, indent=4))



def on_message(client, userdata, message):
    """
    Receive sensor data, evaluate it and publish actuator commands.
    """
    try:
        sensor_data = json.loads(message.payload.decode("utf-8"))

        if not isinstance(sensor_data, dict):
            print("Invalid sensor reading: Expected a JSON object.")
            return

        print("Sensor reading received:")
        print(json.dumps(sensor_data, indent=4))

        # Retrieve the latest settings from PostgreSQL.
        settings = get_control_settings()

        # Evaluate the sensor reading using the saved settings.
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

        print()

    except (json.JSONDecodeError, UnicodeDecodeError):
        print("Error: Received message is not valid JSON.")

    except (KeyError, TypeError, ValueError) as error:
        print(f"Invalid sensor reading: {error}. Skipping message.")

    except Exception as error:
        print(
            f"Error processing sensor reading: {error}. "
            "Skipping message."
        )


def start_control_logic():
    """
    Connect to MQTT and continuously process incoming sensor readings.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.on_connect = on_connect
    client.on_message = on_message

    print("Starting IoT control logic...")
    print(f"Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()

    except KeyboardInterrupt:
        print("\nStopping IoT control logic...")

    finally:
        client.disconnect()
        pool.close()


if __name__ == "__main__":
    start_control_logic()