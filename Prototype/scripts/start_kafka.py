from pathlib import Path
import socket
import subprocess
import sys
import time

from kafka.admin import KafkaAdminClient
from kafka.errors import KafkaError, TopicAlreadyExistsError
from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KAFKA_BOOTSTRAP_SERVERS = "127.0.0.1:9092"
KAFKA_TOPIC = "sensor-telemetry"
DB_PORT = int(
    dotenv_values(PROJECT_ROOT / "Prototype" / ".env").get("DB_PORT") or 5434
)


def start_kafka_services():
    # Start the shared database, MQTT broker, Kafka, and UI.
    subprocess.run([
        'docker', 'compose',
        '--env-file', str(PROJECT_ROOT / "Prototype" / ".env"),
        'up', '-d', '--build', '--remove-orphans',
        'postgres', 'mosquitto', 'kafka',
        'kafka-ui'
    ], cwd=PROJECT_ROOT, check=True)


def start_mqtt_kafka_bridge():
    subprocess.run([
        'docker', 'compose',
        '--env-file', str(PROJECT_ROOT / "Prototype" / ".env"),
        'up', '-d', '--build', '--force-recreate', 'mqtt-kafka-bridge'
    ], cwd=PROJECT_ROOT, check=True)


def initialize_databases():
    subprocess.run([
        'docker', 'compose',
        '--env-file', str(PROJECT_ROOT / "Prototype" / ".env"),
        'run', '--rm', 'database-init'
    ], cwd=PROJECT_ROOT, check=True)


def wait_for_postgres():
    # Wait until PostgreSQL accepts host connections before starting the consumer.
    for attempt in range(30):
        try:
            with socket.create_connection(("localhost", DB_PORT), timeout=2):
                return
        except OSError:
            print(f"Waiting for PostgreSQL... ({attempt + 1}/30)")
            time.sleep(2)

    raise RuntimeError("PostgreSQL did not become ready")


def wait_for_kafka():
    # Wait until Kafka accepts connections from Windows.
    # Verify a Kafka API request, not just an open listener socket.
    last_error = None
    for attempt in range(30):
        admin = None
        try:
            admin = KafkaAdminClient(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                bootstrap_timeout_ms=5000,
                request_timeout_ms=5000,
            )
            admin.describe_cluster()
            return
        except KafkaError as error:
            last_error = error
            print(f"Waiting for Kafka API... ({attempt + 1}/30): {error}")
        finally:
            if admin is not None:
                admin.close()

        if attempt < 29:
            time.sleep(2)

    raise RuntimeError(
        f"Kafka did not become ready through {KAFKA_BOOTSTRAP_SERVERS}: "
        f"{last_error}"
    ) from last_error


def create_kafka_topic():
    last_error = None
    for attempt in range(10):
        admin = None
        try:
            admin = KafkaAdminClient(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                bootstrap_timeout_ms=5000,
                request_timeout_ms=5000,
            )
            try:
                admin.create_topics({
                    KAFKA_TOPIC: {
                        "num_partitions": 1,
                        "replication_factor": 1,
                    }
                })
            except TopicAlreadyExistsError:
                pass

            topic = admin.describe_topics([KAFKA_TOPIC])[0]
            partitions = topic.get("partitions", [])
            if (
                topic.get("error_code") == 0
                and partitions
                and all(
                    partition.get("error_code") == 0
                    and partition.get("leader_id", -1) >= 0
                    and partition.get("leader_id") in partition.get("isr_nodes", [])
                    for partition in partitions
                )
            ):
                return

            last_error = RuntimeError(
                f"Kafka topic {KAFKA_TOPIC} has no elected partition leader"
            )
            print(
                f"Waiting for Kafka topic partition leader... "
                f"({attempt + 1}/10)"
            )
        except KafkaError as error:
            last_error = error
            print(f"Waiting to create Kafka topic... ({attempt + 1}/10)")
        finally:
            if admin is not None:
                admin.close()

        if attempt < 9:
            time.sleep(3)

    raise RuntimeError(
        f"Kafka topic {KAFKA_TOPIC} was not ready after retries: {last_error}"
    ) from last_error


def run_database_consumer():
    # Keep the startup process attached to the active database consumer.
    subprocess.run(
        [sys.executable, "-m", "scripts.database_consumer"],
        cwd=PROJECT_ROOT / "Prototype",
        check=True,
    )


def start_kafka():
    start_kafka_services()
    initialize_databases()
    wait_for_postgres()
    wait_for_kafka()
    create_kafka_topic()
    start_mqtt_kafka_bridge()
    run_database_consumer()


if __name__ == "__main__":
    start_kafka()