from fastapi import APIRouter, HTTPException
from typing import List

from api.models import TelemetryRow, TelemetryCreate, TelemetryUpdate
from api.db import get_connection


router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# GET /telemetry this will return a list of rows from the iot_telemetry_data table with pagination
@router.get("/", response_model=List[TelemetryRow])
# function to list telemetry data with pagination
def list_telemetry(limit: int = 100, offset: int = 0):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT records, ts, device, co, humidity, light,
                lpg, motion, smoke, temp
                FROM iot_telemetry_data
                ORDER BY records
                LIMIT %s OFFSET %s
                """,
                (limit, offset),

            )
            rows = cur.fetchall()
    return [TelemetryRow(
        records=row[0], ts=row[1], device=row[2], co=row[3], humidity=row[4],
        light=row[5], lpg=row[6], motion=row[7], smoke=row[8], temp=row[9]
    )for row in rows]

# GET /telemetry/{record_id} this will return a single row from the iot_telemetry_data table based on the records column
@router.get("/{record_id}", response_model=TelemetryRow)
def get_telemetry(record_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT records, ts, device, co, humidity, light,
                lpg, motion, smoke, temp
                FROM iot_telemetry_data
                WHERE records = %s
                """,
                (record_id,),
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Telemetry data not found")
    return TelemetryRow(
        records=row[0], ts=row[1], device=row[2], co=row[3], humidity=row[4],
        light=row[5], lpg=row[6], motion=row[7], smoke=row[8], temp=row[9]
    )

# POST /telemetry this will insert a new row into the iot_telemetry_data table and return the newly created row with the auto-generated records column
@router.post("/", response_model=TelemetryRow, status_code=201)
def create_telemetry(payload: TelemetryCreate):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO iot_telemetry_data (ts, device, co, humidity, light, lpg, motion, smoke, temp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING records, ts, device, co, humidity, light, lpg, motion, smoke, temp
                """,
                (payload.ts, payload.device, payload.co, payload.humidity,
                 payload.light, payload.lpg, payload.motion, payload.smoke, payload.temp
                ),
            )
            row = cur.fetchone()
            conn.commit()
    return TelemetryRow(
        records=row[0], ts=row[1], device=row[2], co=row[3], humidity=row[4],
        light=row[5], lpg=row[6], motion=row[7], smoke=row[8], temp=row[9]
    )

# PUT /telemetry/{record_id} this will update a single row in the iot_telemetry_data table based on the records column
@router.put("/{record_id}", response_model=TelemetryRow)
def update_telemetry(record_id: int, payload: TelemetryUpdate):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    set_clause = ", ".join(f"{key} = %s" for key in updates.keys())
    values = list(updates.values()) + [record_id]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE iot_telemetry_data
                SET {set_clause}
                WHERE records = %s
                RETURNING records, ts, device, co, humidity, light, lpg, motion, smoke, temp
                """,
                values,
            )
            row = cur.fetchone()
            conn.commit()
    if row is None:
        raise HTTPException(status_code=404, detail="Telemetry data not found")
    return TelemetryRow(
        records=row[0], ts=row[1], device=row[2], co=row[3], humidity=row[4],
        light=row[5], lpg=row[6], motion=row[7], smoke=row[8], temp=row[9]
    )

# DELETE /telemetry/{record_id} this will delete a single row from the iot_telemetry_data table based on the records column
@router.delete("/{record_id}", status_code=204)
def delete_telemetry(record_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM iot_telemetry_data
                WHERE records = %s
                """,
                (record_id,),
            )
            deleted = cur.rowcount
            conn.commit()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Telemetry data not found")
    return None
