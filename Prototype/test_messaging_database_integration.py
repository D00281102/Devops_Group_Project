
import importlib
import psycopg_pool
import sys
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add Prototype folder to the Python import path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import Data_Sensor
# Add scripts folder to the Python import path
SCRIPTS_PATH = Path(__file__).resolve().parent / "scripts"
sys.path.insert(0, str(SCRIPTS_PATH))

# Add scripts folder to the Python import path
SCRIPTS_PATH = Path(__file__).resolve().parent / "scripts"
sys.path.insert(0, str(SCRIPTS_PATH))

import start_kafka

import start_kafka


class TestSensorMessaging(unittest.TestCase):

    def setUp(self):
        self.sensor_row = {
            "ts": "1594512094.0",
            "device": "b8:27:eb:bf:9d:51",
            "co": "0.0049",
            "humidity": "51.0",
            "light": "false",
            "lpg": "0.0076",
            "motion": "false",
            "smoke": "0.0204",
            "temp": "22.7"
        }

    def test_create_sensor_message(self):
        message = Data_Sensor.create_sensor_message(self.sensor_row)

        self.assertEqual(message["device"], "b8:27:eb:bf:9d:51")
        self.assertEqual(message["humidity"], 51.0)
        self.assertEqual(message["temp"], 22.7)
        self.assertFalse(message["light"])
        self.assertFalse(message["motion"])

    def test_sensor_boolean_values(self):
        self.sensor_row["light"] = "true"
        self.sensor_row["motion"] = "true"

        message = Data_Sensor.create_sensor_message(self.sensor_row)

        self.assertTrue(message["light"])
        self.assertTrue(message["motion"])

    def test_publish_sensor_message(self):
        client = MagicMock()

        message = Data_Sensor.create_sensor_message(self.sensor_row)

        Data_Sensor.publish_sensor_message(client, message)

        client.publish.assert_called_once()

        args = client.publish.call_args[0]

        self.assertEqual(args[0], "sensors/telemetry")

        published_message = json.loads(args[1])

        self.assertEqual(published_message, message)

    def test_connect_to_mqtt(self):
        with patch.object(Data_Sensor.mqtt, "Client") as mock_client:
            client = mock_client.return_value

            result = Data_Sensor.connect_to_mqtt()

            mock_client.assert_called_once()
            client.connect.assert_called_once_with("localhost", 1883, 60)
            client.loop_start.assert_called_once()
            self.assertEqual(result, client)

class TestKafkaIntegration(unittest.TestCase):

    def test_wait_for_kafka(self):
        with patch.object(start_kafka.socket, "create_connection") as mock_socket:
            start_kafka.wait_for_kafka()

            mock_socket.assert_called_once_with(
                ("localhost", 9092), timeout=2
            )

    def test_create_kafka_topic(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Topic created"
        mock_result.stderr = ""

        with patch.object(
            start_kafka.subprocess,
            "run",
            return_value=mock_result
        ) as mock_run:

            start_kafka.create_kafka_topic()

            mock_run.assert_called_once()

            command = mock_run.call_args[0][0]

            self.assertIn("sensor-telemetry", command)
            self.assertIn("--create", command)
            self.assertIn("localhost:9092", command)

    def test_create_existing_kafka_topic(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Topic already exists"
        mock_result.stderr = ""

        with patch.object(
            start_kafka.subprocess,
            "run",
            return_value=mock_result
        ):
            start_kafka.create_kafka_topic()

    def test_wait_for_kafka_connect(self):
        with patch.object(start_kafka, "urlopen") as mock_urlopen:
            start_kafka.wait_for_connect()

            mock_urlopen.assert_called_once_with(
                "http://localhost:8083/", timeout=3
            )

    def test_start_kafka_connector(self):
        with patch.object(start_kafka, "urlopen") as mock_urlopen:
            start_kafka.start_kafka_connector()

            mock_urlopen.assert_called_once()

            request = mock_urlopen.call_args[0][0]

            self.assertEqual(
                request.full_url,
                "http://localhost:8083/connectors"
            )
            self.assertEqual(request.method, "POST")

            connector_data = json.loads(request.data)

            self.assertEqual(connector_data["name"], "mqtt-source")
            self.assertEqual(
                connector_data["config"]["kafka.topic"],
                "sensor-telemetry"
            )

    def test_start_kafka_consumer(self):
        with patch.object(
            start_kafka.subprocess,
            "Popen"
        ) as mock_popen:

            start_kafka.start_kafka_consumer()

            mock_popen.assert_called_once()

            command = mock_popen.call_args[0][0]

            self.assertIn("sensor-telemetry", command)
            self.assertIn("--from-beginning", command)

class TestKafkaIntegration(unittest.TestCase):

    def test_wait_for_kafka(self):
        with patch.object(start_kafka.socket, "create_connection") as mock_socket:
            start_kafka.wait_for_kafka()

            mock_socket.assert_called_once_with(
                ("localhost", 9092), timeout=2
            )

    def test_create_kafka_topic(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Topic created"
        mock_result.stderr = ""

        with patch.object(
            start_kafka.subprocess,
            "run",
            return_value=mock_result
        ) as mock_run:

            start_kafka.create_kafka_topic()

            mock_run.assert_called_once()

            command = mock_run.call_args[0][0]

            self.assertIn("sensor-telemetry", command)
            self.assertIn("--create", command)
            self.assertIn("localhost:9092", command)

    def test_create_existing_kafka_topic(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Topic already exists"
        mock_result.stderr = ""

        with patch.object(
            start_kafka.subprocess,
            "run",
            return_value=mock_result
        ):
            start_kafka.create_kafka_topic()

    def test_wait_for_kafka_connect(self):
        with patch.object(start_kafka, "urlopen") as mock_urlopen:
            start_kafka.wait_for_connect()

            mock_urlopen.assert_called_once_with(
                "http://localhost:8083/", timeout=3
            )

    def test_start_kafka_connector(self):
        with patch.object(start_kafka, "urlopen") as mock_urlopen:
            start_kafka.start_kafka_connector()

            mock_urlopen.assert_called_once()

            request = mock_urlopen.call_args[0][0]

            self.assertEqual(
                request.full_url,
                "http://localhost:8083/connectors"
            )
            self.assertEqual(request.method, "POST")

            connector_data = json.loads(request.data)

            self.assertEqual(connector_data["name"], "mqtt-source")
            self.assertEqual(
                connector_data["config"]["kafka.topic"],
                "sensor-telemetry"
            )

    def test_start_kafka_consumer(self):
        with patch.object(
            start_kafka.subprocess,
            "Popen"
        ) as mock_popen:

            start_kafka.start_kafka_consumer()

            mock_popen.assert_called_once()

            command = mock_popen.call_args[0][0]

            self.assertIn("sensor-telemetry", command)
            self.assertIn("--from-beginning", command)

class TestDatabaseIntegration(unittest.TestCase):

    def setUp(self):
        # Load the real database module without using the API test mock
        import importlib.util

        db_path = Path(__file__).parent / "api" / "db.py"

        spec = importlib.util.spec_from_file_location(
            "real_api_db",
            db_path
        )

        self.api_db = importlib.util.module_from_spec(spec)

        with patch.object(
            psycopg_pool,
            "ConnectionPool"
        ) as mock_pool_class:

            spec.loader.exec_module(self.api_db)
            self.mock_pool = mock_pool_class.return_value

        self.connection = MagicMock()

        self.connection_context = MagicMock()
        self.connection_context.__enter__.return_value = self.connection
        self.connection_context.__exit__.return_value = False

        self.mock_pool.connection.return_value = self.connection_context

    def test_database_connection(self):
        with self.api_db.get_connection() as conn:
            self.assertEqual(conn, self.connection)

        self.mock_pool.connection.assert_called_once()

    def test_database_connection_context_closes(self):
        with self.api_db.get_connection():
            pass

        self.connection_context.__exit__.assert_called_once()

    def test_database_connection_error(self):
        self.connection_context.__enter__.side_effect = (
            RuntimeError("Database connection failed")
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Database connection failed"
        ):
            with self.api_db.get_connection():
                pass

    def test_database_connection_pool_settings(self):
        self.assertEqual(self.api_db.pool, self.mock_pool)


if __name__ == "__main__":
    unittest.main(verbosity=2)
