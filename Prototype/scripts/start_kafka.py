import json
from pathlib import Path
import socket
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from start_mqtt import start_mqtt

KAFKA_HOME = r"C:\kafka"
CONNECT_URL = "http://localhost:8083"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def start_kafka_KafkaUI():
    # Start Kafka and Kafka UI using subprocess
    subprocess.run([
        'docker', 'compose', 'up', '-d', 'kafka', 'kafka-ui', 'kafka-connect'
    ], cwd=PROJECT_ROOT, check=True)


def wait_for_kafka():
    # Wait until Kafka accepts connections from Windows.
    for attempt in range(30):
        try:
            with socket.create_connection(("localhost", 9092), timeout=2):
                return
        except OSError:
            print(f"Waiting for Kafka... ({attempt + 1}/30)")
            time.sleep(2)

    raise RuntimeError("Kafka did not become ready")


def create_kafka_topic():
    # Create the topic used for sensor telemetry.
    command = [
        rf"{KAFKA_HOME}\bin\windows\kafka-topics.bat",
        '--create',
        '--topic', 'sensor-telemetry',
        '--bootstrap-server', 'localhost:9092',
        '--partitions', '1',
        '--replication-factor', '1'
    ]

    for attempt in range(10):
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0 or "already exists" in result.stdout.lower():
            return

        print(f"Waiting to create Kafka topic... ({attempt + 1}/10)")
        time.sleep(3)

    raise RuntimeError(result.stderr or result.stdout)


def wait_for_connect():
    # Wait until Kafka Connect's REST API responds.
    for attempt in range(30):
        try:
            with urlopen(f"{CONNECT_URL}/", timeout=3):
                return
        except (OSError, URLError):
            print(f"Waiting for Kafka Connect... ({attempt + 1}/30)")
            time.sleep(2)

    raise RuntimeError("Kafka Connect did not become ready")


def start_kafka_connector():
    # Register the MQTT source connector with Kafka Connect.
    with open(PROJECT_ROOT / "connector-config.json", "r", encoding="utf-8") as file:
        connector = json.load(file)

    request = Request(
        f"{CONNECT_URL}/connectors",
        data=json.dumps(connector).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urlopen(request, timeout=10):
            print("Kafka MQTT connector registered.")
    except HTTPError as error:
        if error.code == 409:
            print("Kafka MQTT connector is already registered.")
        else:
            raise


def start_kafka_consumer():
    # Display messages from the Kafka sensor topic.
    return subprocess.Popen([
        rf"{KAFKA_HOME}\bin\windows\kafka-console-consumer.bat",
        '--bootstrap-server', 'localhost:9092',
        '--topic', 'sensor-telemetry',
        '--from-beginning',
        '--property',
        'value.deserializer=org.apache.kafka.common.serialization.StringDeserializer'
    ])


def start_kafka():
    start_mqtt()
    start_kafka_KafkaUI()
    wait_for_kafka()
    create_kafka_topic()
    wait_for_connect()
    start_kafka_connector()
    start_kafka_consumer()


if __name__ == "__main__":
    start_kafka()