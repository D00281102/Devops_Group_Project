from fastapi import APIRouter, HTTPException
from typing import List

from api.models import TelemetryRow
from api.db import get_connection


router = APIRouter(prefix="/telemetry", tags=["telemetry"])

# GET /telemetry
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
