from unittest.mock import Mock

from scripts.mqtt_kafka_bridge import forward_mqtt_message


def test_forward_mqtt_message_publishes_original_payload():
    producer = Mock()
    payload = b'{"device":"sensor-1"}'

    forward_mqtt_message(producer, "sensor-telemetry", payload)

    producer.send.assert_called_once_with("sensor-telemetry", value=payload)
    producer.send.return_value.get.assert_called_once_with(timeout=30)


if __name__ == "__main__":
    test_forward_mqtt_message_publishes_original_payload()
    print("MQTT-to-Kafka bridge tests passed.")
