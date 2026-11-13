import json
import paho.mqtt.client as mqtt
import os

# MQTT configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
<<<<<<< HEAD
# Each simulator listens for commands for its own building.
BUILDING_ID = int(os.getenv("BUILDING_ID", "1"))
ACTUATOR_TOPIC = f"buildings/{BUILDING_ID}/actuators/commands"
=======
ACTUATOR_TOPIC = "actuators/commands"
>>>>>>> main


def on_connect(client, userdata, flags, reason_code, properties):
    """
    Subscribe to the actuator command topic after connecting to MQTT.
    """
    print(f"Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
    client.subscribe(ACTUATOR_TOPIC)
    print(f"Subscribed to MQTT topic: {ACTUATOR_TOPIC}")
    print("Waiting for actuator commands...\n")


def simulate_actuator(command):
    """
    Simulate an actuator responding to a control command.
    """
    actuator = command.get("actuator")
    action = command.get("action")
    reason = command.get("reason")

    print("Actuator command received:")
    print(f"Actuator: {actuator}")
    print(f"Action: {action}")
    print(f"Reason: {reason}")

    if actuator == "fan":
        print(f"Simulated Fan: {action}")

    elif actuator == "dehumidifier":
        print(f"Simulated Dehumidifier: {action}")

    elif actuator == "light":
        print(f"Simulated Light: {action}")

    else:
        print("Unknown actuator")

    print()


def on_message(client, userdata, message):
    """
    Receive and process actuator commands from MQTT.
    """
    try:
        command = json.loads(message.payload.decode("utf-8"))

        # Ignore commands that belong to another building.
        if command.get("building_id") != BUILDING_ID:
            print(f"Ignoring command for another building: {command.get('building_id')}")
            return

        simulate_actuator(command)

    except json.JSONDecodeError:
        print("Error: Received actuator command is not valid JSON.")


def start_actuator_simulator():
    """
    Connect to MQTT and listen for actuator commands.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    print("Starting IoT actuator simulator...")
    client.loop_forever()


if __name__ == "__main__":
    start_actuator_simulator()