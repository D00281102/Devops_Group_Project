
from fastapi import APIRouter, Depends, HTTPException

from api.control_db import get_control_connection
from api.models import ControlSettings
from api.auth import get_current_user

control_router = APIRouter(tags=["control-settings"])


def get_user_building(cur, user_id):
    cur.execute(
        """
        SELECT b.building_id, b.building_name
        FROM buildings b
        JOIN building_members bm
            ON b.building_id = bm.building_id
        WHERE bm.user_id = %s
          AND bm.status = 'approved'
          AND bm.role = 'admin'
        ORDER BY b.building_id
        LIMIT 1
        """,
        (user_id,)
    )

    building = cur.fetchone()

    if building is None:
        raise HTTPException(
            status_code=403,
            detail="No approved building administrator access found"
        )

    return building


@control_router.get("/control-settings", response_model=ControlSettings)
def get_control_settings(
    current_user: dict = Depends(get_current_user)
):
    with get_control_connection() as conn:
        with conn.cursor() as cur:
            building = get_user_building(
                cur, current_user["user_id"]
            )

            building_id = building[0]

            cur.execute(
                """
                SELECT temperature_threshold, humidity_threshold,
                       light_enabled, updated_at
                FROM control_settings
                WHERE building_id = %s
                """,
                (building_id,)
            )

            row = cur.fetchone()

            if row is None:
                cur.execute(
                    """
                    INSERT INTO control_settings (
                        temperature_threshold,
                        humidity_threshold,
                        light_enabled,
                        building_id
                    )
                    VALUES (25, 70, TRUE, %s)
                    RETURNING temperature_threshold, humidity_threshold,
                              light_enabled, updated_at
                    """,
                    (building_id,)
                )
                row = cur.fetchone()
                conn.commit()

    return ControlSettings(
        temperature_threshold=row[0],
        humidity_threshold=row[1],
        light_enabled=row[2],
        updated_at=row[3].isoformat() if row[3] else None,
    )


@control_router.put("/control-settings", response_model=ControlSettings)
def update_control_settings(
    payload: ControlSettings,
    current_user: dict = Depends(get_current_user)
):
    with get_control_connection() as conn:
        with conn.cursor() as cur:
            building = get_user_building(
                cur, current_user["user_id"]
            )

            building_id = building[0]

            cur.execute(
                """
                INSERT INTO control_settings (
                    temperature_threshold,
                    humidity_threshold,
                    light_enabled,
                    building_id,
                    updated_at
                )
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (building_id)
                WHERE building_id IS NOT NULL
                DO UPDATE SET
                    temperature_threshold = EXCLUDED.temperature_threshold,
                    humidity_threshold = EXCLUDED.humidity_threshold,
                    light_enabled = EXCLUDED.light_enabled,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING temperature_threshold, humidity_threshold,
                          light_enabled, updated_at
                """,
                (
                    payload.temperature_threshold,
                    payload.humidity_threshold,
                    payload.light_enabled,
                    building_id,
                ),
            )

            row = cur.fetchone()
            conn.commit()

    return ControlSettings(
        temperature_threshold=row[0],
        humidity_threshold=row[1],
        light_enabled=row[2],
        updated_at=row[3].isoformat() if row[3] else None,
    )
