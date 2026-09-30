import json
import paho.mqtt.client as mqtt

# MQTT configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
SENSOR_TOPIC = "sensors/telemetry"
ACTUATOR_TOPIC = "actuators/commands"

def on_connect(client, userdata, flags, reason_code, properties):
    """
    Subscribe to the sensor telemetry topic after connecting to MQTT.
    """
    print(f"Connected to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
    client.subscribe(SENSOR_TOPIC)
    print(f"Subscribed to MQTT topic: {SENSOR_TOPIC}")
    print("Waiting for sensor readings...\n")

def evaluate_sensor_data(sensor_data):
    """
    Evaluate sensor readings and generate actuator commands.
    """
    commands = []

    if sensor_data["temp"] >= 25:
        commands.append({
            "actuator": "fan",
            "action": "ON",
            "reason": "High temperature detected"
        })

    if sensor_data["humidity"] >= 70:
        commands.append({
            "actuator": "dehumidifier",
            "action": "ON",
            "reason": "High humidity detected"
        })

    if sensor_data["light"]:
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

        print("Sensor reading received:")
        print(json.dumps(sensor_data, indent=4))

        commands = evaluate_sensor_data(sensor_data)

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