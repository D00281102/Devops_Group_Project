import json
import getpass
from datetime import datetime, timezone

import psycopg2
from kafka import KafkaConsumer


# Ask for the database password without storing it in the code
db_password = getpass.getpass("PostgreSQL password: ")

# Connect to PostgreSQL
connection = psycopg2.connect(
    host="localhost",
    port=5432,
    database="iot_sensor_db",
    user="postgres",
    password=db_password
)

cursor = connection.cursor()

# Connect to the Kafka topic
consumer = KafkaConsumer(
    "sensor-telemetry",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="latest",
    group_id="database-consumer"
)

print("Kafka -> Database consumer started.")
print("Waiting for sensor data...")


for message in consumer:
    try:
        # Convert Kafka message bytes into JSON
        raw_value = message.value.decode("utf-8")
        data = json.loads(raw_value)
       

        # Convert Unix timestamp to PostgreSQL timestamp
        timestamp = datetime.fromtimestamp(
            float(data["ts"]),
            tz=timezone.utc
        )

        # Insert sensor reading into database
        cursor.execute(
            """
            INSERT INTO sensor_data
            (ts, device, co, humidity, light, lpg, motion, smoke, temp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                timestamp,
                data["device"],
                data["co"],
                data["humidity"],
                data["light"],
                data["lpg"],
                data["motion"],
                data["smoke"],
                data["temp"]
            )
        )

        connection.commit()

        print(f"Stored sensor reading from {data['device']}")

    except Exception as error:
        connection.rollback()
        print(f"Error processing message: {error}")