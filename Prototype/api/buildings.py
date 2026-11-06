from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4
from api.models import BuildingCreate, BuildingJoin
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


@buildings_router.post("/join", status_code=201)
def request_building_membership(
    payload: BuildingJoin,
    current_user: dict = Depends(get_current_user)
):
    building_code = payload.building_code.strip()

    if not building_code:
        raise HTTPException(status_code=422, detail="Building code cannot be empty")

    with get_auth_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT building_id FROM buildings WHERE building_code = %s",
                (building_code,)
            )
            building = cur.fetchone()

            if not building:
                raise HTTPException(status_code=404, detail="Invalid building code")

            building_id = building[0]

            cur.execute(
                """
                SELECT status FROM building_members
                WHERE user_id = %s AND building_id = %s
                """,
                (current_user["user_id"], building_id)
            )

            if cur.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail="You already have a membership or request for this building"
                )

            cur.execute(
                """
                INSERT INTO building_members
                    (user_id, building_id, role, status)
                VALUES (%s, %s, 'member', 'pending')
                """,
                (current_user["user_id"], building_id)
            )

    return {
        "message": "Building access request submitted",
        "building_id": building_id,
        "status": "pending"
    }


@buildings_router.get("/{building_id}/requests")
def get_pending_membership_requests(
    building_id: int,
    current_user: dict = Depends(get_current_user)
):
    with get_auth_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM building_members
                WHERE building_id = %s
                  AND user_id = %s
                  AND role = 'admin'
                  AND status = 'approved'
                """,
                (building_id, current_user["user_id"])
            )

            if not cur.fetchone():
                raise HTTPException(
                    status_code=403,
                    detail="Only approved building admins can view membership requests"
                )

            cur.execute(
                """
                SELECT membership_id, user_id, role, status
                FROM building_members
                WHERE building_id = %s
                  AND status = 'pending'
                ORDER BY membership_id
                """,
                (building_id,)
            )

            requests = cur.fetchall()

    return {
        "building_id": building_id,
        "requests": [
            {
                "membership_id": row[0],
                "user_id": row[1],
                "role": row[2],
                "status": row[3]
            }
            for row in requests
        ]
    }
