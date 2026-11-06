import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import control_db
from api.auth import create_access_token
from api.auth_db import get_auth_connection
from api.buildings import buildings_router
from api.control_routes import control_router


load_dotenv(".env")

# Connect ONLY to the isolated test database.
control_db.CONTROL_DB_HOST = "127.0.0.1"
control_db.CONTROL_DB_PORT = 5435
control_db.CONTROL_DB_NAME = "controldb_combined_test"
control_db.CONTROL_DB_USER = "postgres"
control_db.CONTROL_DB_PASSWORD = os.getenv("AUTH_DB_PASSWORD")

app = FastAPI()
app.include_router(buildings_router)
app.include_router(control_router)
client = TestClient(app)


def request(method, path, user_id, **kwargs):
    token = create_access_token(user_id)
    return client.request(
        method,
        path,
        headers={"Authorization": f"Bearer {token}"},
        **kwargs,
    )


def run_test():
    # Safety check: never run against the main database.
    with get_auth_connection() as conn:
        auth_db = conn.execute("SELECT current_database()").fetchone()[0]

    with control_db.get_control_connection() as conn:
        settings_db = conn.execute("SELECT current_database()").fetchone()[0]

    assert auth_db == "controldb_combined_test"
    assert settings_db == "controldb_combined_test"

    print("PASS: Both connections use the isolated test database")

    # Use a unique building name for each test run.
    building_name = "SCRUM-163 Test " + uuid.uuid4().hex[:8]

    # User 1 creates a building.
    response = request(
        "POST", "/buildings/", 1,
        json={"building_name": building_name},
    )
    assert response.status_code == 201, response.text

    building = response.json()["building"]
    building_id = building["building_id"]
    building_code = building["building_code"]

    print("PASS: Building created (201)")

    # User 2 requests membership.
    response = request(
        "POST", "/buildings/join", 2,
        json={"building_code": building_code},
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "pending"

    print("PASS: Membership request created (201, pending)")

    # Pending user must not access control settings.
    response = request(
        "GET", f"/control-settings?building_id={building_id}", 2
    )
    assert response.status_code == 403, response.text

    print("PASS: Pending user denied access (403)")

    # Admin retrieves the pending membership.
    response = request(
        "GET", f"/buildings/{building_id}/requests", 1
    )
    assert response.status_code == 200, response.text

    requests = response.json()["requests"]
    membership_id = next(
        item["membership_id"]
        for item in requests
        if item["user_id"] == 2
    )

    print("PASS: Admin can view pending requests (200)")

    # Admin approves user 2.
    response = request(
        "PATCH",
        f"/buildings/{building_id}/requests/{membership_id}",
        1,
        json={"status": "approved"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["membership"]["status"] == "approved"

    print("PASS: Admin approved membership (200)")

    # Approved member can read settings.
    response = request(
        "GET", f"/control-settings?building_id={building_id}", 2
    )
    assert response.status_code == 200, response.text

    print("PASS: Approved member can read settings (200)")

    # Ordinary member cannot update settings.
    response = request(
        "PUT", f"/control-settings?building_id={building_id}", 2,
        json={
            "temperature_threshold": 28,
            "humidity_threshold": 75,
            "light_enabled": False,
        },
    )
    assert response.status_code == 403, response.text

    print("PASS: Ordinary member cannot update settings (403)")

    # Building admin updates settings.
    response = request(
        "PUT", f"/control-settings?building_id={building_id}", 1,
        json={
            "temperature_threshold": 28,
            "humidity_threshold": 75,
            "light_enabled": False,
        },
    )
    assert response.status_code == 200, response.text

    print("PASS: Admin updated control settings (200)")

    # Verify values were saved in PostgreSQL.
    with control_db.get_control_connection() as conn:
        row = conn.execute(
            """
            SELECT temperature_threshold,
                   humidity_threshold,
                   light_enabled
            FROM control_settings
            WHERE building_id = %s
            """,
            (building_id,),
        ).fetchone()

    assert row is not None
    assert float(row[0]) == 28
    assert float(row[1]) == 75
    assert row[2] is False

    print("PASS: Control settings saved in PostgreSQL")
    print()
    print("SCRUM-163: ALL INTEGRATION TESTS PASSED")
    print("Test building ID:", building_id)


if __name__ == "__main__":
    run_test()