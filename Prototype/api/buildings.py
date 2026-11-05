from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4
from api.models import BuildingCreate
from api.auth import get_current_user
from api.auth_db import get_auth_connection

buildings_router = APIRouter(prefix="/buildings", tags=["Buildings"])


@buildings_router.get("/")
def get_my_buildings(current_user: dict = Depends(get_current_user)):

    with get_auth_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT b.building_id, b.building_name,
                       b.building_code, bm.role
                FROM buildings b
                JOIN building_members bm
                    ON b.building_id = bm.building_id
                WHERE bm.user_id = %s
                  AND bm.status = 'approved'
                ORDER BY b.building_id
                """,
                (current_user["user_id"],)
            )

            buildings = cur.fetchall()

    return {
        "buildings": [
            {
                "building_id": row[0],
                "building_name": row[1],
                "building_code": row[2],
                "role": row[3]
            }
            for row in buildings
        ]
    }

@buildings_router.post("/", status_code=201)
def create_building(
    payload: BuildingCreate,
    current_user: dict = Depends(get_current_user)
):
    building_name = payload.building_name.strip()

    if not building_name:
        raise HTTPException(
            status_code=422,
            detail="Building name cannot be empty"
        )

    building_code = "BLD-" + uuid4().hex[:16].upper()

    with get_auth_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO buildings
                    (building_name, building_code, created_by)
                VALUES (%s, %s, %s)
                RETURNING building_id, building_name, building_code
                """,
                (
                    building_name,
                    building_code,
                    current_user["user_id"]
                )
            )

            building = cur.fetchone()

            cur.execute(
                """
                INSERT INTO building_members
                    (user_id, building_id, role, status)
                VALUES (%s, %s, 'admin', 'approved')
                """,
                (current_user["user_id"], building[0])
            )

    return {
        "message": "Building created successfully",
        "building": {
            "building_id": building[0],
            "building_name": building[1],
            "building_code": building[2],
            "role": "admin"
        }
    }
