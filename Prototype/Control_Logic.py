import json
import paho.mqtt.client as mqtt

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
SENSOR_TOPIC = "sensors/telemetry"


def on_connect(client, userdata, flags, reason_code, properties):
    """
    Subscribe to the sensor telemetry topic after connecting to MQTT.
    """
    print(f"Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
    client.subscribe(SENSOR_TOPIC)
    print(f"Subscribed to MQTT topic: {SENSOR_TOPIC}")
    print("Waiting for sensor readings...\n")


def on_message(client, userdata, message):
    """
    Receive and decode sensor messages from MQTT.
    """
    try:
        sensor_data = json.loads(message.payload.decode("utf-8"))

        print("Sensor reading received:")
        print(json.dumps(sensor_data, indent=4))
        print()

    except json.JSONDecodeError:
        print("Error: Received message is not valid JSON.")


def start_control_logic():
    """
    Connect to MQTT and listen for incoming sensor readings.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    print("Starting IoT control logic...")
    client.loop_forever()


if __name__ == "__main__":
    start_control_logic()