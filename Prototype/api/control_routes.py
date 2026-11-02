from fastapi import APIRouter, Depends, HTTPException

from api.control_db import get_control_connection
from api.models import ControlSettings
from api.auth import get_current_user
from api.auth_db import get_auth_connection


control_router = APIRouter(tags=["control-settings"])


def check_building_access(building_id: int, current_user: dict):
    """
    Check whether the logged-in user has approved access to a building.
    Return their building role if access is allowed.
    """
    with get_auth_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT role
                FROM building_members
                WHERE user_id = %s
                  AND building_id = %s
                  AND status = 'approved'
                """,
                (current_user["user_id"], building_id)
            )

            membership = cur.fetchone()

    if membership is None:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this building"
        )

    return membership[0]


# Legacy endpoints are disabled to prevent bypassing building permissions.
# The frontend must use the building-specific endpoints instead.

@control_router.get(
    "/control-settings",
    response_model=ControlSettings,
    include_in_schema=False
)
def get_control_settings():
    raise HTTPException(
        status_code=410,
        detail="Use /buildings/{building_id}/control-settings instead"
    )


@control_router.put(
    "/control-settings",
    response_model=ControlSettings,
    include_in_schema=False
)
def update_control_settings(payload: ControlSettings):
    raise HTTPException(
        status_code=410,
        detail="Use /buildings/{building_id}/control-settings instead"
    )


# Get settings for a building the user belongs to.

@control_router.get(
    "/buildings/{building_id}/control-settings",
    response_model=ControlSettings
)
def get_building_control_settings(
    building_id: int,
    current_user: dict = Depends(get_current_user)
):
    # Check that the user belongs to this building.
    check_building_access(building_id, current_user)

    with get_control_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT temperature_threshold,
                       humidity_threshold,
                       light_enabled,
                       updated_at
                FROM control_settings
                WHERE building_id = %s
                """,
                (building_id,)
            )

            row = cur.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="No control settings found for this building"
        )

    return ControlSettings(
        temperature_threshold=row[0],
        humidity_threshold=row[1],
        light_enabled=row[2],
        updated_at=row[3].isoformat() if row[3] else None,
    )


# Update settings for a building.
# Only approved building admins can make changes.

@control_router.put(
    "/buildings/{building_id}/control-settings",
    response_model=ControlSettings
)
def update_building_control_settings(
    building_id: int,
    payload: ControlSettings,
    current_user: dict = Depends(get_current_user)
):
    # Check the user's role in this building.
    role = check_building_access(building_id, current_user)

    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only building admins can update control settings"
        )

    with get_control_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO control_settings (
                    building_id,
                    temperature_threshold,
                    humidity_threshold,
                    light_enabled,
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
                RETURNING
                    temperature_threshold,
                    humidity_threshold,
                    light_enabled,
                    updated_at
                """,
                (
                    building_id,
                    payload.temperature_threshold,
                    payload.humidity_threshold,
                    payload.light_enabled,
                )
            )

            row = cur.fetchone()
            conn.commit()

    return ControlSettings(
        temperature_threshold=row[0],
        humidity_threshold=row[1],
        light_enabled=row[2],
        updated_at=row[3].isoformat() if row[3] else None,
    )
