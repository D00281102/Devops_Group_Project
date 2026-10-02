from fastapi import Request
from fastapi.responses import JSONResponse
from psycopg import OperationalError, IntegrityError

# Custom exception handler for database connection errors
async def db_connection_error_handler(request: Request, exc: OperationalError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Database unavailable. Please try again later.", "error": str(exc)},
    )

# Custom exception handler for database integrity errors
async def db_integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409,
        content={"detail": "Database constraint violated. Please check your input.", "error": str(exc)},
    )