from fastapi import APIRouter

from api.control_db import get_control_connection
from api.models import ControlSettings

control_router = APIRouter(tags=["control-settings"])


@control_router.get("/control-settings", response_model=ControlSettings)
def get_control_settings():
    with get_control_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT temperature_threshold, humidity_threshold, light_enabled
                FROM control_settings
                WHERE id = 1
                """
            )
            row = cur.fetchone()

            if row is None:
                cur.execute(
                    """
                    INSERT INTO control_settings (
                        id, temperature_threshold, humidity_threshold,
                        light_enabled
                    )
                    VALUES (1, 25, 70, TRUE)
                    RETURNING temperature_threshold, humidity_threshold,
                              light_enabled
                    """
                )
                row = cur.fetchone()
                conn.commit()

    return ControlSettings(
        temperature_threshold=row[0],
        humidity_threshold=row[1],
        light_enabled=row[2],
    )


@control_router.put("/control-settings", response_model=ControlSettings)
def update_control_settings(payload: ControlSettings):
    with get_control_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO control_settings (
                    id, temperature_threshold, humidity_threshold,
                    light_enabled, updated_at
                )
                VALUES (1, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (id)
                DO UPDATE SET
                    temperature_threshold = EXCLUDED.temperature_threshold,
                    humidity_threshold = EXCLUDED.humidity_threshold,
                    light_enabled = EXCLUDED.light_enabled,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING temperature_threshold, humidity_threshold,
                          light_enabled
                """,
                (
                    payload.temperature_threshold,
                    payload.humidity_threshold,
                    payload.light_enabled,
                ),
            )
            row = cur.fetchone()
            conn.commit()

    return ControlSettings(
        temperature_threshold=row[0],
        humidity_threshold=row[1],
        light_enabled=row[2],
    )
