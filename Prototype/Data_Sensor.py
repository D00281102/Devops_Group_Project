import csv
import json
import os
from pathlib import Path
import time

import paho.mqtt.client as mqtt

# MQTT configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = 1883
MQTT_TOPIC = "sensors/telemetry"

# Path to the IoT telemetry dataset
DATA_FILE = Path(__file__).parent / "data" / "iot_telemetry_data.csv"

# Replay the dataset faster than real time
REPLAY_SPEED = 10

# Limit used while testing the simulator
MAX_READINGS = 10


def create_sensor_message(row):
    """
    Convert a CSV row into a structured sensor message.
    """
    return {
        "ts": float(row["ts"]),
        "device": row["device"],
        "co": float(row["co"]),
        "humidity": float(row["humidity"]),
        "light": row["light"].lower() == "true",
        "lpg": float(row["lpg"]),
        "motion": row["motion"].lower() == "true",
        "smoke": float(row["smoke"]),
        "temp": float(row["temp"])
    }


def connect_to_mqtt():
    """
    Connect to the MQTT broker.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    print(f"Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")

    return client


def publish_sensor_message(client, sensor_message):
    """
    Publish a sensor reading to the MQTT broker.
    """
    payload = json.dumps(sensor_message)

    client.publish(
        MQTT_TOPIC,
        payload
    )

    print(f"Published to MQTT topic: {MQTT_TOPIC}")


def replay_sensor_data():
    """
    Replay sensor readings using the timing from the original dataset.
    """
    previous_timestamp = None

    client = connect_to_mqtt()

    with open(DATA_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        print("Starting IoT sensor simulation...\n")

        for reading_number, row in enumerate(reader, start=1):
            sensor_message = create_sensor_message(row)
            current_timestamp = sensor_message["ts"]

            if previous_timestamp is not None:
                delay = (current_timestamp - previous_timestamp) / REPLAY_SPEED

                if delay > 0:
                    time.sleep(delay)

            publish_sensor_message(client, sensor_message)

            print(f"Simulated reading {reading_number}:")
            print(json.dumps(sensor_message, indent=4))
            print()

            previous_timestamp = current_timestamp

            if reading_number == MAX_READINGS:
                break

    client.loop_stop()
    client.disconnect()

    print("Sensor simulation complete.")


if __name__ == "__main__":
    replay_sensor_data()