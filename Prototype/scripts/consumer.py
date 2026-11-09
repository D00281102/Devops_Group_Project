import json
import os

import psycopg
from kafka import KafkaConsumer, TopicPartition, OffsetAndMetadata


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "kafka:9093"
)
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sensor-telemetry")
KAFKA_GROUP_ID = os.getenv(
    "KAFKA_GROUP_ID", "telemetry-postgres-writer"
)
MAX_MESSAGES = int(os.getenv("KAFKA_MAX_MESSAGES", "20"))

REQUIRED_FIELDS = [
    "ts", "device", "co", "humidity", "light",
    "lpg", "motion", "smoke", "temp"
]


def commit_message(consumer, message):
    partition = TopicPartition(message.topic, message.partition)
    consumer.commit({
        partition: OffsetAndMetadata(message.offset + 1, "")
    })


def convert_boolean(value, field):
    if isinstance(value, bool):
        return value

    if isinstance(value, int) and value in (0, 1):
        return bool(value)

    raise ValueError(
        f"Invalid Boolean value for {field}: {value}"
    )


def main():
    print("Starting Kafka to PostgreSQL consumer...")
    print("Kafka topic:", KAFKA_TOPIC)
    print("Consumer group:", KAFKA_GROUP_ID)
    print("Maximum messages:", MAX_MESSAGES)

    conn = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

    consumer = KafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False
    )

    consumer.subscribe([KAFKA_TOPIC])

    processed = 0
    idle_checks = 0

    try:
        while MAX_MESSAGES == 0 or processed < MAX_MESSAGES:
            messages = consumer.poll(timeout_ms=1000, max_records=1)

            if not messages:
                idle_checks += 1

                if MAX_MESSAGES != 0 and idle_checks >= 15:
                    print("No more messages available. Stopping.")
                    break

                continue

            idle_checks = 0

            for records in messages.values():
                for message in records:
                    try:
                        data = json.loads(message.value.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        print(f"Skipping invalid JSON message: {e}")
                        commit_message(consumer, message)
                        continue

                    missing = [
                        field for field in REQUIRED_FIELDS
                        if field not in data
                    ]

                    if missing:
                        print(f"Skipping message with missing fields: {missing}")
                        commit_message(consumer, message)
                        continue

                    try:
                        light = convert_boolean(data["light"], "light")
                        motion = convert_boolean(data["motion"], "motion")
                    except ValueError as e:
                        print(f"Skipping invalid sensor values: {e}")
                        commit_message(consumer, message)
                        continue

                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO iot_telemetry_data
                            (ts, device, co, humidity, light,
                             lpg, motion, smoke, temp)
                            VALUES (%s, %s, %s, %s, %s,
                                    %s, %s, %s, %s)
                            """,
                            (
                                data["ts"],
                                data["device"],
                                data["co"],
                                data["humidity"],
                                light,
                                data["lpg"],
                                motion,
                                data["smoke"],
                                data["temp"]
                            )
                        )

                    conn.commit()
                    commit_message(consumer, message)

                    processed += 1

                    print(
                        f"Inserted telemetry record {processed}: "
                        f"{data['device']}"
                    )

    finally:
        consumer.close()
        conn.close()

    print(f"Consumer finished. Records inserted: {processed}")


if __name__ == "__main__":
    main()