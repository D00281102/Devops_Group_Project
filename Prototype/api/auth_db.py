
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

# Load environment variables from Prototype/.env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_auth_connection():
    """Connect to the authentication database."""

    required_settings = [
        "AUTH_DB_HOST",
        "AUTH_DB_PORT",
        "AUTH_DB_NAME",
        "AUTH_DB_USER",
        "AUTH_DB_PASSWORD",
    ]

    missing = [
        setting for setting in required_settings
        if not os.getenv(setting)
    ]

    if missing:
        raise RuntimeError(
            "Missing authentication database settings: "
            + ", ".join(missing)
        )

    return psycopg.connect(
        host=os.getenv("AUTH_DB_HOST"),
        port=int(os.getenv("AUTH_DB_PORT")),
        dbname=os.getenv("AUTH_DB_NAME"),
        user=os.getenv("AUTH_DB_USER"),
        password=os.getenv("AUTH_DB_PASSWORD"),
	connect_timeout=5,
    )
