from fastapi import FastAPI
from psycopg import OperationalError, IntegrityError

from api.routes import router
from api.errors import db_connection_error_handler, db_integrity_error_handler

# Create FastAPI app instance and register exception handlers for database errors
app = FastAPI(title="IoT Telemetry API", version="0.1.0")
app.add_exception_handler(OperationalError, db_connection_error_handler)
app.add_exception_handler(IntegrityError, db_integrity_error_handler)
# Include the router for API endpoints
app.include_router(router)

# Define a root endpoint for health checks
@app.get("/")
def root():
    return {"status": "ok"}