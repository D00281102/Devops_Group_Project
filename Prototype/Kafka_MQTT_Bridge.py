"""
Bridge Kafka actuator commands to building-specific MQTT topics.
"""

import json
import os
import time

from kafka import KafkaConsumer
import paho.mqtt.client as mqtt


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_COMMAND_TOPIC = os.getenv("KAFKA_COMMAND_TOPIC", "actuator-commands")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))


def validate_command(command):
    """Validate the actuator command and its building ID."""
    if not isinstance(command, dict):
        raise ValueError("Command must be a JSON object")

    building_id = command.get("building_id")
    if isinstance(building_id, bool) or not isinstance(building_id, int) or building_id <= 0:
        raise ValueError("Invalid building_id")

    if not isinstance(command.get("actuator"), str) or not command["actuator"]:
        raise ValueError("Missing actuator")

    if not isinstance(command.get("action"), str) or not command["action"]:
        raise ValueError("Missing action")

    return building_id


def publish_to_mqtt(client, command):
    """Publish a validated command to its building's MQTT topic."""
    building_id = validate_command(command)
    topic = f"buildings/{building_id}/actuators/commands"

    result = client.publish(topic, json.dumps(command), qos=1)
    result.wait_for_publish(timeout=10)

    if not result.is_published():
        raise RuntimeError("MQTT delivery was not acknowledged")

    print(f"Published MQTT command to: {topic}", flush=True)
    print(json.dumps(command, indent=4), flush=True)


def start_bridge():
    """Forward Kafka commands to MQTT with retry handling."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    consumer = None

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        consumer = KafkaConsumer(
            KAFKA_COMMAND_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="kafka-mqtt-actuator-bridge",
            auto_offset_reset="earliest",
            enable_auto_commit=False
        )

        print(f"Listening for Kafka commands on: {KAFKA_COMMAND_TOPIC}", flush=True)

        for message in consumer:
            try:
                command = json.loads(message.value.decode("utf-8"))
                validate_command(command)

            except (ValueError, UnicodeDecodeError, TypeError) as error:
                print(f"Skipping invalid command: {error}", flush=True)
                consumer.commit()
                continue

            while True:
                try:
                    publish_to_mqtt(client, command)
                    consumer.commit()
                    break

                except Exception as error:
                    print(f"MQTT publishing failed: {error}. Retrying...", flush=True)
                    time.sleep(5)

    except KeyboardInterrupt:
        print("Stopping Kafka-to-MQTT bridge...", flush=True)

    finally:
        if consumer is not None:
            consumer.close()
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    start_bridge()
