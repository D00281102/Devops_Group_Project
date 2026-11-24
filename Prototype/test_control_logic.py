import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the Prototype folder to Python's import path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Prevent a real PostgreSQL connection pool from being created
sys.modules["api.db"] = MagicMock()

from Control_Logic import evaluate_sensor_data, on_message


class TestControlLogic(unittest.TestCase):

    def setUp(self):
        self.settings = {
            "temperature_threshold": 25,
            "humidity_threshold": 70,
            "light_enabled": True
        }

    # Test 1: All three actuators should activate
    def test_all_actuators_activate(self):
        sensor_data = {
            "temp": 26,
            "humidity": 75,
            "light": True
        }

        commands = evaluate_sensor_data(sensor_data, self.settings)

        self.assertEqual(len(commands), 3)
        self.assertEqual(commands[0]["actuator"], "fan")
        self.assertEqual(commands[1]["actuator"], "dehumidifier")
        self.assertEqual(commands[2]["actuator"], "light")

    # Test 2: Only the fan should activate
    def test_temperature_control(self):
        sensor_data = {
            "temp": 30,
            "humidity": 50,
            "light": False
        }

        commands = evaluate_sensor_data(sensor_data, self.settings)

        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["actuator"], "fan")
        self.assertEqual(commands[0]["action"], "ON")

    # Test 3: Only the dehumidifier should activate
    def test_humidity_control(self):
        sensor_data = {
            "temp": 20,
            "humidity": 85,
            "light": False
        }

        commands = evaluate_sensor_data(sensor_data, self.settings)

        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["actuator"], "dehumidifier")
        self.assertEqual(commands[0]["action"], "ON")

    # Test 4: Only the light should activate
    def test_light_control(self):
        sensor_data = {
            "temp": 20,
            "humidity": 50,
            "light": True
        }

        commands = evaluate_sensor_data(sensor_data, self.settings)

        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["actuator"], "light")
        self.assertEqual(commands[0]["action"], "ON")

    # Test 5: No actuator should activate
    def test_no_actuator_commands(self):
        sensor_data = {
            "temp": 20,
            "humidity": 50,
            "light": False
        }

        commands = evaluate_sensor_data(sensor_data, self.settings)

        self.assertEqual(len(commands), 0)

    # Test 6: Exact threshold values should activate the actuators
    def test_threshold_boundaries(self):
        sensor_data = {
            "temp": 25,
            "humidity": 70,
            "light": False
        }

        commands = evaluate_sensor_data(sensor_data, self.settings)

        self.assertEqual(len(commands), 2)
        self.assertEqual(commands[0]["actuator"], "fan")
        self.assertEqual(commands[1]["actuator"], "dehumidifier")

    # Test 7: Check the command reasons
    def test_command_reasons(self):
        sensor_data = {
            "temp": 30,
            "humidity": 85,
            "light": True
        }

        commands = evaluate_sensor_data(sensor_data, self.settings)

        self.assertEqual(
            commands[0]["reason"],
            "High temperature detected"
        )
        self.assertEqual(
            commands[1]["reason"],
            "High humidity detected"
        )
        self.assertEqual(
            commands[2]["reason"],
            "Light detected"
        )

    # Test 8: Custom temperature threshold
    def test_custom_temperature_threshold(self):
        sensor_data = {
            "temp": 28,
            "humidity": 50,
            "light": False
        }

        settings = self.settings.copy()
        settings["temperature_threshold"] = 30

        commands = evaluate_sensor_data(sensor_data, settings)

        self.assertEqual(len(commands), 0)

    # Test 9: Custom humidity threshold
    def test_custom_humidity_threshold(self):
        sensor_data = {
            "temp": 20,
            "humidity": 65,
            "light": False
        }

        settings = self.settings.copy()
        settings["humidity_threshold"] = 60

        commands = evaluate_sensor_data(sensor_data, settings)

        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["actuator"], "dehumidifier")

    # Test 10: Light should remain off when disabled
    def test_light_disabled(self):
        sensor_data = {
            "temp": 20,
            "humidity": 50,
            "light": True
        }

        settings = self.settings.copy()
        settings["light_enabled"] = False

        commands = evaluate_sensor_data(sensor_data, settings)

        self.assertEqual(len(commands), 0)

    
    # Test 11: Invalid JSON message should be handled safely
    @patch("Control_Logic.get_control_settings")
    def test_invalid_json_message(self, mock_settings):
        message = MagicMock()
        message.payload = b"invalid json"

        client = MagicMock()

        on_message(client, None, message)

        mock_settings.assert_not_called()
        client.publish.assert_not_called()

    # Test 12: Invalid sensor data should be rejected
    @patch("Control_Logic.get_control_settings")
    def test_invalid_sensor_data(self, mock_settings):
        message = MagicMock()
        message.payload = b'["invalid", "sensor", "data"]'

        client = MagicMock()

        on_message(client, None, message)

        mock_settings.assert_not_called()
        client.publish.assert_not_called()

    # Test 13: Database error should be handled safely
    @patch("Control_Logic.get_control_settings")
    def test_database_error_handling(self, mock_settings):
        message = MagicMock()
        message.payload = b'{"temp": 32, "humidity": 65, "light": true}'

        mock_settings.side_effect = RuntimeError("Database unavailable")

        client = MagicMock()

        on_message(client, None, message)

        mock_settings.assert_called_once()
        client.publish.assert_not_called()

    # Test 14: No commands should be published when settings fail
    @patch("Control_Logic.get_control_settings")
    def test_no_commands_when_settings_unavailable(self, mock_settings):
        message = MagicMock()
        message.payload = b'{"temp": 32, "humidity": 65, "light": true}'

        mock_settings.side_effect = Exception("Settings unavailable")

        client = MagicMock()

        on_message(client, None, message)

        client.publish.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
