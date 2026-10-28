import json
import logging

from kafka import KafkaConsumer
from kafka.structs import OffsetAndMetadata, TopicPartition
from pydantic import ValidationError

from api.db import get_connection
from api.models import TelemetryCreate

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "sensor-telemetry"
CONSUMER_GROUP = "iot-telemetry-database"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def store_telemetry(payload: TelemetryCreate) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO iot_telemetry_data
                    (ts, device, co, humidity, light, lpg, motion, smoke, temp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    payload.ts,
                    payload.device,
                    payload.co,
                    payload.humidity,
                    payload.light,
                    payload.lpg,
                    payload.motion,
                    payload.smoke,
                    payload.temp,
                ),
            )
        conn.commit()


def consume_telemetry() -> None:
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=CONSUMER_GROUP,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )

    try:
        for message in consumer:
            try:
                payload = TelemetryCreate.model_validate(json.loads(message.value))
            except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
                raise ValueError(
                    "Invalid telemetry at "
                    f"{message.topic}[{message.partition}] offset {message.offset}"
                ) from error

            store_telemetry(payload)
            consumer.commit(
                {
                    TopicPartition(message.topic, message.partition): OffsetAndMetadata(
                        message.offset + 1, ""
                    )
                }
            )
            logger.info(
                "Stored telemetry from %s[%s] offset %s",
                message.topic,
                message.partition,
                message.offset,
            )
    finally:
        consumer.close()


if __name__ == "__main__":
    consume_telemetry()
