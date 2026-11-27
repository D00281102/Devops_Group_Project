from unittest.mock import patch

from kafka.errors import KafkaTimeoutError, TopicAlreadyExistsError

from scripts import start_kafka


def test_wait_for_kafka_waits_for_api_readiness():
    with (
        patch.object(start_kafka, "KafkaAdminClient") as admin_client,
        patch.object(start_kafka.time, "sleep") as sleep,
    ):
        admin_client.side_effect = [
            KafkaTimeoutError("not ready"),
            admin_client.return_value,
        ]
        start_kafka.wait_for_kafka()

    assert admin_client.call_count == 2
    admin_client.assert_called_with(
        bootstrap_servers="127.0.0.1:9092",
        bootstrap_timeout_ms=5000,
        request_timeout_ms=5000,
    )
    admin_client.return_value.describe_cluster.assert_called_once_with()
    admin_client.return_value.close.assert_called_once_with()
    sleep.assert_called_once_with(2)


def test_start_kafka_waits_for_topic_before_starting_bridge():
    calls = []
    with (
        patch.object(
            start_kafka, "start_kafka_services",
            side_effect=lambda: calls.append("services"),
        ),
        patch.object(
            start_kafka, "initialize_databases",
            side_effect=lambda: calls.append("databases"),
        ),
        patch.object(
            start_kafka, "wait_for_postgres",
            side_effect=lambda: calls.append("postgres"),
        ),
        patch.object(
            start_kafka, "wait_for_kafka",
            side_effect=lambda: calls.append("kafka"),
        ),
        patch.object(
            start_kafka, "create_kafka_topic",
            side_effect=lambda: calls.append("topic"),
        ),
        patch.object(
            start_kafka, "start_mqtt_kafka_bridge",
            side_effect=lambda: calls.append("bridge"),
        ),
        patch.object(
            start_kafka, "run_database_consumer",
            side_effect=lambda: calls.append("consumer"),
        ),
    ):
        start_kafka.start_kafka()

    assert calls == [
        "services",
        "databases",
        "postgres",
        "kafka",
        "topic",
        "bridge",
        "consumer",
    ]


def test_create_kafka_topic_uses_admin_client():
    with patch.object(start_kafka, "KafkaAdminClient") as admin_client:
        admin_client.return_value.describe_topics.return_value = [{
            "error_code": 0,
            "partitions": [{
                "error_code": 0,
                "leader_id": 1,
                "isr_nodes": [1],
            }],
        }]
        start_kafka.create_kafka_topic()

    admin_client.assert_called_once_with(
        bootstrap_servers="127.0.0.1:9092",
        bootstrap_timeout_ms=5000,
        request_timeout_ms=5000,
    )
    admin_client.return_value.create_topics.assert_called_once_with({
        "sensor-telemetry": {
            "num_partitions": 1,
            "replication_factor": 1,
        }
    })
    admin_client.return_value.describe_topics.assert_called_once_with([
        "sensor-telemetry"
    ])
    admin_client.return_value.close.assert_called_once_with()


def test_create_kafka_topic_waits_for_partition_leader():
    with (
        patch.object(start_kafka, "KafkaAdminClient") as admin_client,
        patch.object(start_kafka.time, "sleep") as sleep,
    ):
        admin_client.return_value.describe_topics.side_effect = [
            [{
                "error_code": 0,
                "partitions": [{
                    "error_code": 0,
                    "leader_id": -1,
                    "isr_nodes": [],
                }],
            }],
            [{
                "error_code": 0,
                "partitions": [{
                    "error_code": 0,
                    "leader_id": 1,
                    "isr_nodes": [1],
                }],
            }],
        ]
        start_kafka.create_kafka_topic()

    assert admin_client.call_count == 2
    assert admin_client.return_value.describe_topics.call_count == 2
    assert admin_client.return_value.close.call_count == 2
    sleep.assert_called_once_with(3)


def test_create_kafka_topic_accepts_existing_topic():
    with patch.object(start_kafka, "KafkaAdminClient") as admin_client:
        admin_client.return_value.create_topics.side_effect = (
            TopicAlreadyExistsError("sensor-telemetry")
        )
        admin_client.return_value.describe_topics.return_value = [{
            "error_code": 0,
            "partitions": [{
                "error_code": 0,
                "leader_id": 1,
                "isr_nodes": [1],
            }],
        }]
        start_kafka.create_kafka_topic()

    admin_client.return_value.describe_topics.assert_called_once_with([
        "sensor-telemetry"
    ])
    admin_client.return_value.close.assert_called_once_with()


if __name__ == "__main__":
    test_wait_for_kafka_waits_for_api_readiness()
    test_start_kafka_waits_for_topic_before_starting_bridge()
    test_create_kafka_topic_uses_admin_client()
    test_create_kafka_topic_waits_for_partition_leader()
    test_create_kafka_topic_accepts_existing_topic()
