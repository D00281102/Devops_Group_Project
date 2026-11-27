import logging
import os

from kafka import KafkaProducer
from kafka.errors import KafkaError
import paho.mqtt.client as mqtt

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "127.0.0.1:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sensor-telemetry")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "sensors/telemetry")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def forward_mqtt_message(
    producer: KafkaProducer, topic: str, payload: bytes
) -> None:
    producer.send(topic, value=payload).get(timeout=30)


def start_bridge() -> None:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        acks="all",
        retries=5,
    )
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            logger.error("MQTT connection failed: %s", reason_code)
            return

        result, _ = client.subscribe(MQTT_TOPIC, qos=0)
        if result != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Could not subscribe to MQTT topic %s", MQTT_TOPIC)
            return

        logger.info("Subscribed to MQTT topic %s", MQTT_TOPIC)

    def on_message(client, userdata, message):
        try:
            forward_mqtt_message(producer, KAFKA_TOPIC, message.payload)
        except KafkaError:
            logger.exception(
                "Could not forward MQTT message from %s to Kafka topic %s",
                message.topic,
                KAFKA_TOPIC,
            )
            return

        logger.info(
            "Forwarded MQTT message from %s to Kafka topic %s",
            message.topic,
            KAFKA_TOPIC,
        )

    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    try:
        client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.loop_forever(retry_first_connection=True)
    finally:
        client.disconnect()
        producer.flush(timeout=30)
        producer.close(timeout=30)


if __name__ == "__main__":
    start_bridge()
