
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from psycopg import OperationalError, IntegrityError

# Add Prototype folder to the Python import path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Prevent the API from creating a real database connection pool
db_module = types.ModuleType("api.db")
db_module.get_connection = MagicMock()
db_module.pool = MagicMock()
sys.modules["api.db"] = db_module

from api.main import app
import api.routes as api_routes
import api.analytics_routes as analytics_routes


class TestControlAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def mock_database(self, fetchone=None, fetchall=None,
                      rowcount=1, execute_error=None):

        conn = MagicMock()
        cursor = MagicMock()

        connection_context = MagicMock()
        connection_context.__enter__.return_value = conn
        connection_context.__exit__.return_value = False

        conn.cursor.return_value.__enter__.return_value = cursor

        cursor.fetchone.return_value = fetchone
        cursor.fetchall.return_value = fetchall or []
        cursor.rowcount = rowcount

        if execute_error:
            cursor.execute.side_effect = execute_error

        database_patch = patch.object(
            api_routes,
            "get_connection",
            return_value=connection_context
        )
        database_patch.start()
        self.addCleanup(database_patch.stop)

        return cursor, conn

    def sample_row(self):
        return (
            1, 1700000000.0, "sensor-1", 0.5,
            45.0, True, 0.1, False, 0.2, 22.5
        )

    def sample_payload(self):
        return {
            "ts": 1700000000.0,
            "device": "sensor-1",
            "co": 0.5,
            "humidity": 45.0,
            "light": True,
            "lpg": 0.1,
            "motion": False,
            "smoke": 0.2,
            "temp": 22.5
        }

    def test_root_endpoint(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_get_telemetry_list(self):
        self.mock_database(fetchall=[self.sample_row()])

        response = self.client.get("/telemetry/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["device"], "sensor-1")

    def test_get_telemetry_with_pagination(self):
        cursor, _ = self.mock_database(fetchall=[self.sample_row()])

        response = self.client.get("/telemetry/?limit=10&offset=5")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            cursor.execute.call_args[0][1],
            (10, 5)
        )

    def test_get_single_telemetry_record(self):
        self.mock_database(fetchone=self.sample_row())

        response = self.client.get("/telemetry/1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["records"], 1)

    def test_get_missing_record(self):
        self.mock_database(fetchone=None)

        response = self.client.get("/telemetry/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"],
            "Telemetry data not found"
        )

    def test_create_telemetry(self):
        cursor, conn = self.mock_database(
            fetchone=self.sample_row()
        )

        response = self.client.post(
            "/telemetry/",
            json=self.sample_payload()
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["device"], "sensor-1")
        cursor.execute.assert_called_once()
        conn.commit.assert_called_once()

    def test_create_telemetry_with_invalid_data(self):
        response = self.client.post(
            "/telemetry/",
            json={"device": "sensor-1"}
        )

        self.assertEqual(response.status_code, 422)

    def test_update_telemetry(self):
        cursor, conn = self.mock_database(
            fetchone=self.sample_row()
        )

        response = self.client.put(
            "/telemetry/1",
            json={"temp": 24.5}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["records"], 1)
        cursor.execute.assert_called_once()
        conn.commit.assert_called_once()

    def test_update_with_empty_data(self):
        response = self.client.put(
            "/telemetry/1",
            json={}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"],
            "No fields to update"
        )

    def test_update_missing_record(self):
        self.mock_database(fetchone=None)

        response = self.client.put(
            "/telemetry/999",
            json={"temp": 24.5}
        )

        self.assertEqual(response.status_code, 404)

    def test_delete_telemetry(self):
        cursor, conn = self.mock_database(rowcount=1)

        response = self.client.delete("/telemetry/1")

        self.assertEqual(response.status_code, 204)
        cursor.execute.assert_called_once()
        conn.commit.assert_called_once()

    def test_delete_missing_record(self):
        self.mock_database(rowcount=0)

        response = self.client.delete("/telemetry/999")

        self.assertEqual(response.status_code, 404)

    def test_database_connection_error(self):
        self.mock_database(
            execute_error=OperationalError("Database unavailable")
        )

        response = self.client.get("/telemetry/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            "Database unavailable. Please try again later."
        )

    def test_database_integrity_error(self):
        self.mock_database(
            execute_error=IntegrityError("Constraint violation")
        )

        response = self.client.post(
            "/telemetry/",
            json=self.sample_payload()
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["detail"],
            "Database constraint violated. Please check your input."
        )

    def test_analytics_endpoint(self):
        expected_result = {"temperature": {"average": 22.5}}

        with patch.object(
            analytics_routes,
            "get_analytics_results",
            return_value=expected_result
        ):
            response = self.client.get("/analytics/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_result)

    def test_invalid_telemetry_record_id(self):
        response = self.client.get("/telemetry/not-a-number")
        self.assertEqual(response.status_code, 422)

    def test_invalid_pagination_parameters(self):
        response = self.client.get("/telemetry/?limit=invalid")
        self.assertEqual(response.status_code, 422)

    def test_update_with_invalid_field_type(self):
        response = self.client.put(
            "/telemetry/1",
            json={"temp": "not-a-number"}
        )
        self.assertEqual(response.status_code, 422)

    def test_empty_telemetry_list(self):
        self.mock_database(fetchall=[])

        response = self.client.get("/telemetry/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_telemetry_response_fields(self):
        self.mock_database(fetchone=self.sample_row())

        response = self.client.get("/telemetry/1")

        self.assertEqual(response.status_code, 200)

        expected_fields = {
            "records", "ts", "device", "co", "humidity",
            "light", "lpg", "motion", "smoke", "temp"
        }

        self.assertEqual(set(response.json().keys()), expected_fields)
        self.assertIsInstance(response.json()["device"], str)
        self.assertIsInstance(response.json()["temp"], float)

    def test_analytics_endpoint_error(self):
        with patch.object(
            analytics_routes,
            "get_analytics_results",
            side_effect=RuntimeError("Analytics unavailable")
        ):
            with self.assertRaises(RuntimeError):
                self.client.get("/analytics/")


if __name__ == "__main__":
    unittest.main(verbosity=2)
