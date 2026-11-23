import json
import os
import paho.mqtt.client as mqtt

# MQTT configuration
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# Listen for actuator commands from all buildings.
ACTUATOR_TOPIC = "buildings/+/actuators/commands"


def on_connect(client, userdata, flags, reason_code, properties):
    """
    Connect to MQTT and subscribe to all building actuator topics.
    """
    if reason_code == 0:
        print(f"Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(ACTUATOR_TOPIC)
        print(f"Subscribed to MQTT topic: {ACTUATOR_TOPIC}")
        print("Waiting for actuator commands...\n")
    else:
        print(f"MQTT connection failed: {reason_code}")


def simulate_actuator(command, building_id):
    """
    Simulate an actuator responding to a building-specific command.
    """
    actuator = command.get("actuator")
    action = command.get("action")
    reason = command.get("reason")

    print("Actuator command received:")
    print(f"Building ID: {building_id}")
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
    Receive actuator commands for any building.
    Validate the MQTT topic and building ID before processing.
    """
    try:
        # Extract the building ID from the MQTT topic.
        topic_parts = message.topic.split("/")

        if (
            len(topic_parts) != 4
            or topic_parts[0] != "buildings"
            or topic_parts[2] != "actuators"
            or topic_parts[3] != "commands"
        ):
            print(f"Invalid actuator topic: {message.topic}")
            return

        try:
            building_id = int(topic_parts[1])
        except ValueError:
            print("Invalid building ID in MQTT topic.")
            return

        if building_id <= 0:
            print("Invalid building ID in MQTT topic.")
            return

        # Decode the actuator command.
        command = json.loads(message.payload.decode("utf-8"))

        if not isinstance(command, dict):
            print("Invalid actuator command format.")
            return

        # Confirm that the payload matches the MQTT building.
        command_building_id = command.get("building_id")

        if type(command_building_id) is not int or command_building_id != building_id:
            print(
                f"Building ID mismatch: topic={building_id}, "
                f"payload={command_building_id}. Ignoring command."
            )
            return

        simulate_actuator(command, building_id)

    except (json.JSONDecodeError, UnicodeDecodeError):
        print("Error: Received actuator command is not valid JSON.")


def start_actuator_simulator():
    """
    Connect to MQTT and simulate actuator commands for all buildings.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.on_connect = on_connect
    client.on_message = on_message

    print("Starting dynamic IoT actuator simulator...")

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    start_actuator_simulator()
