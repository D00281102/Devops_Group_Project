
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add the Prototype folder to Python's import path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Prevent a real PostgreSQL connection pool from being created
sys.modules["api.db"] = MagicMock()

from Control_Logic import evaluate_sensor_data


class TestControlLogic(unittest.TestCase):

    # Test 1: All three actuators should activate
    def test_all_actuators_activate(self):
        sensor_data = {
            "temp": 26,
            "humidity": 75,
            "light": True
        }

        commands = evaluate_sensor_data(sensor_data)

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

        commands = evaluate_sensor_data(sensor_data)

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

        commands = evaluate_sensor_data(sensor_data)

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

        commands = evaluate_sensor_data(sensor_data)

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

        commands = evaluate_sensor_data(sensor_data)

        self.assertEqual(len(commands), 0)

    # Test 6: Exact threshold values should activate the fan and dehumidifier
    def test_threshold_boundaries(self):
        sensor_data = {
            "temp": 25,
            "humidity": 70,
            "light": False
        }

        commands = evaluate_sensor_data(sensor_data)

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

        commands = evaluate_sensor_data(sensor_data)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
