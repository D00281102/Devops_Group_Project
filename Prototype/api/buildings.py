from fastapi import APIRouter, Depends
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
