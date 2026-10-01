import subprocess
import time


KAFKA_HOME = r"C:\kafka"


def start_kafka_KafkaUI():
    # Start Kafka and Kafka UI using subprocess
    kafka_process = subprocess.Popen([
        'docker', 'compose', 'up', '-d', 'kafka', 'kafka-ui'
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


def start_kafka():
    start_kafka_KafkaUI()
    create_kafka_topic()