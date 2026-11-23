
from fastapi import APIRouter
from api.db import get_connection
from api.models import ControlSettings

control_router = APIRouter(tags=["control-settings"])


@control_router.get("/control-settings", response_model=ControlSettings)
def get_control_settings():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT temperature_threshold, humidity_threshold,
                       light_enabled, updated_at
                FROM control_settings
                WHERE id = 1
            """)
            row = cur.fetchone()

    return ControlSettings(
        temperature_threshold=row[0],
        humidity_threshold=row[1],
        light_enabled=row[2],
        updated_at=row[3].isoformat()
    )


@control_router.put("/control-settings", response_model=ControlSettings)
def update_control_settings(payload: ControlSettings):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE control_settings
                SET temperature_threshold = %s,
                    humidity_threshold = %s,
                    light_enabled = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
                RETURNING temperature_threshold, humidity_threshold,
                          light_enabled, updated_at
            """, (
                payload.temperature_threshold,
                payload.humidity_threshold,
                payload.light_enabled
            ))

            row = cur.fetchone()
            conn.commit()

    return ControlSettings(
        temperature_threshold=row[0],
        humidity_threshold=row[1],
        light_enabled=row[2],
        updated_at=row[3].isoformat()
    )
