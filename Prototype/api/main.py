from fastapi import FastAPI
from psycopg import OperationalError, IntegrityError

from api.routes import router
from api.analytics_routes import analytics_router
from api.errors import db_connection_error_handler, db_integrity_error_handler
from api.control_routes import control_router
from api.auth import router as auth_router
from api.buildings import buildings_router
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(title="IoT Telemetry API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.add_exception_handler(OperationalError, db_connection_error_handler)
app.add_exception_handler(IntegrityError, db_integrity_error_handler)

# Include API routers
app.include_router(router)
app.include_router(analytics_router)
app.include_router(control_router)
app.include_router(auth_router)
app.include_router(buildings_router)


@app.get("/")
def root():
    return {"status": "ok"}
