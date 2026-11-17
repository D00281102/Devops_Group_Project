import csv
import json
from pathlib import Path
import time
import paho.mqtt.client as mqtt
import os

# MQTT configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = "sensors/telemetry"

# Path to the IoT telemetry dataset
BUILDING_ID = int(os.getenv("BUILDING_ID", "1"))
DEVICE_ID = os.getenv("DEVICE_ID", "")
DATASET_PATH = os.getenv("DATASET_PATH", "data/iot_telemetry_data.csv")

DATA_FILE = Path(DATASET_PATH)
if not DATA_FILE.is_absolute():
    DATA_FILE = Path(__file__).parent / DATA_FILE


# Replay the dataset faster than real time
REPLAY_SPEED = 10

# Limit used while testing the simulator
MAX_READINGS = 10


def create_sensor_message(row):
    """
    Normalise different CSV formats into one sensor message.
    """

    # Match different CSV column names
    columns = {key.strip().lower(): value for key, value in row.items() if key}

    def get_value(*names):
        for name in names:
            value = columns.get(name.lower())
            if value is not None and str(value).strip():
                return str(value).strip()
        return None

    def get_number(*names):
        value = get_value(*names)
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def get_boolean(*names):
        value = get_value(*names)
        if value is None:
            return None
        if value.lower() in ("true", "1", "yes"):
            return True
        if value.lower() in ("false", "0", "no"):
            return False
        return None

    # Preserve original device IDs unless overridden
    device = DEVICE_ID or get_value("device", "device_id")

    return {
        "building_id": BUILDING_ID,
        "ts": get_number("ts", "timestamp"),
        "device": device,
        "co": get_number("co"),
        "humidity": get_number("humidity"),
        "light": get_boolean("light"),
        "lpg": get_number("lpg"),
        "motion": get_boolean("motion"),
        "smoke": get_number("smoke"),
        "temp": get_number("temp", "temperature")
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

    with open(DATA_FILE, "r", newline="", encoding="utf-8-sig") as file:
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
