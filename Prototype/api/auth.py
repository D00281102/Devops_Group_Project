
import os
from datetime import datetime, timedelta, timezone

import jwt
import psycopg
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from api.auth_db import get_auth_connection

router = APIRouter(prefix="/auth", tags=["Authentication"])

password_hash = PasswordHash.recommended()
security = HTTPBearer()

# User registration details
class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )
    password: str = Field(min_length=8, max_length=128)


# User login details
class LoginRequest(BaseModel):
    email: str = Field(
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )
    password: str = Field(min_length=8, max_length=128)


# Hash a password before saving it
def hash_password(password: str) -> str:
    return password_hash.hash(password)


# Check a password against its stored hash
def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(password, hashed_password)
    except (ValueError, TypeError, UnknownHashError):
        return False


# Create a JWT token
def create_access_token(user_id: int) -> str:
    secret_key = os.getenv("AUTH_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("AUTH_SECRET_KEY is missing")

    expiry = datetime.now(timezone.utc) + timedelta(minutes=30)

    payload = {
        "sub": str(user_id),
        "exp": expiry
    }

    return jwt.encode(payload, secret_key, algorithm="HS256")

# Verify JWT token and identify the logged-in user
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    secret_key = os.getenv("AUTH_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("AUTH_SECRET_KEY is missing")

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=["HS256"]
        )

        user_id = int(payload.get("sub"))

    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    with get_auth_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, full_name, email
                FROM users
                WHERE user_id = %s
                """,
                (user_id,)
            )

            account = cur.fetchone()

    if account is None:
        raise HTTPException(
            status_code=401,
            detail="User account not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "user_id": account[0],
        "full_name": account[1],
        "email": account[2]
    }


# Register a new user
@router.post("/register", status_code=201)
def register_user(user: RegisterRequest):

    email = user.email.strip().lower()
    hashed_password = hash_password(user.password)

    try:
        with get_auth_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (full_name, email, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING user_id, full_name, email, created_at
                    """,
                    (user.full_name.strip(), email, hashed_password)
                )

                new_user = cur.fetchone()

    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="Email address is already registered"
        )

    return {
        "message": "User registered successfully",
        "user": {
            "user_id": new_user[0],
            "full_name": new_user[1],
            "email": new_user[2],
            "created_at": new_user[3]
        }
    }


# Log in an existing user
@router.post("/login")
def login_user(user: LoginRequest):

    email = user.email.strip().lower()

    with get_auth_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT user_id, full_name, email, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            account = cur.fetchone()

    if account is None or not verify_password(user.password, account[3]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(account[0])

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": account[0],
            "full_name": account[1],
            "email": account[2]
        }
    }

# Get details of the currently logged-in user
@router.get("/me")
def get_my_account(
    current_user: dict = Depends(get_current_user)
):
    return {
        "message": "Authenticated user retrieved successfully",
        "user": current_user
    }
