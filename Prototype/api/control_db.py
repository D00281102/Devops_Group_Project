import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# Load the environment variables from Prototype/.env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Control settings database configuration
CONTROL_DB_HOST = os.getenv("CONTROL_DB_HOST", "localhost")
CONTROL_DB_PORT = int(os.getenv("CONTROL_DB_PORT", "5432"))
CONTROL_DB_NAME = os.getenv("CONTROL_DB_NAME", "control_settings_db")
CONTROL_DB_USER = os.getenv("CONTROL_DB_USER", "postgres")
CONTROL_DB_PASSWORD = os.getenv("CONTROL_DB_PASSWORD")


def get_control_connection():
    if not CONTROL_DB_PASSWORD:
        raise RuntimeError(
            "CONTROL_DB_PASSWORD is missing from Prototype/.env"
        )

    return psycopg.connect(
        host=CONTROL_DB_HOST,
        port=CONTROL_DB_PORT,
        dbname=CONTROL_DB_NAME,
        user=CONTROL_DB_USER,
        password=CONTROL_DB_PASSWORD,
    )
