import subprocess
import time

def start_kafka_KafkaUI():
    # Start Kafka and Kafka UI using subprocess
    kafka_process = subprocess.Popen(['docker-compose', 'up', '-d', 'kafka', 'kafka-ui'])
    time.sleep(10)  # Wait for Kafka to start

    return kafka_process

 #Start Kafka connector
