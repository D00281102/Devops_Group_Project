import json
import subprocess
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


KAFKA_HOME = r"C:\kafka"
CONNECT_URL = "http://localhost:8083"


def start_kafka_KafkaUI():
    # Start Kafka and Kafka UI using subprocess
    kafka_process = subprocess.Popen([
        'docker', 'compose', 'up', '-d', 'kafka', 'kafka-ui', 'kafka-connect'
    ])
    time.sleep(10)  # Wait for Kafka to start

    return kafka_process


def create_kafka_topic():
    # Create the topic used for sensor telemetry.
    subprocess.run([
        rf"{KAFKA_HOME}\bin\windows\kafka-topics.bat",
        '--create',
        '--topic', 'sensor-telemetry',
        '--bootstrap-server', 'localhost:9092',
        '--partitions', '1',
        '--replication-factor', '1'
    ], check=False)


def start_kafka_connector():
    # Register the MQTT source connector with Kafka Connect.
    time.sleep(10)

    with open("connector-config.json", "r", encoding="utf-8") as file:
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


def start_kafka():
    start_kafka_KafkaUI()
    create_kafka_topic()
    start_kafka_connector()


if __name__ == "__main__":
    start_kafka()