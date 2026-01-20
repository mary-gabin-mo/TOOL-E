"""Minimal FastAPI server exposing /api/auth/login backed by MySQL.

Replace the naive password comparison with hashed verification once real
credentials are stored securely (e.g., bcrypt or Argon2).
"""

import os
import secrets
from typing import Dict, Optional

import mysql.connector
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(title="TOOL-E API")


# Allow the Vite dev server to make credentialed requests.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginPayload(BaseModel):
    ucid: str
    password: str


class User(BaseModel):
    ucid: str
    FirstName: str
    LastName: str


class LoginResponse(BaseModel):
    token: str
    user: User


def build_db_pool():
    # MYSQL Connection Pool configs
    config = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "toole"),
        "pool_name": "toole_pool",
        "pool_size": int(os.environ.get("DB_POOL_SIZE", "5")),
        "raise_on_warnings": False,
        "auth_plugin": os.environ.get("DB_AUTH_PLUGIN", None),
    }

    # Drop keys with None to appease mysql.connector.
    config = {k: v for k, v in config.items() if v is not None}

    try:
        return mysql.connector.pooling.MySQLConnectionPool(**config)
    except mysql.connector.Error as exc:
        # Surface a clear error at startup if DB is unreachable/misconfigured.
        raise RuntimeError(f"Failed to create MySQL pool: {exc}") from exc


db_pool = build_db_pool()


def fetch_user(ucid: str) -> Optional[Dict[str, str]]:
    # Get single user row by UCID
    ucid_normalized = ucid.strip()
    conn = db_pool.get_connection()
    try:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                """
                SELECT ucid, FirstName, LastName, password
                FROM users
                WHERE LOWER(ucid) = LOWER(%s)
                LIMIT 1
                """,
                (ucid_normalized,),
            )
            return cur.fetchone()
    finally:
        conn.close()


@app.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginPayload) -> LoginResponse:
    # Validate credentials against the DB row; swap to hashed verify for real use
    user_record = fetch_user(payload.ucid)

    if not user_record or payload.password != user_record["password"]:
        # Deliberately vague to avoid leaking which field failed.
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_urlsafe(32)

    return LoginResponse(
        token=token,
        user=User(
            ucid=payload.ucid,
            FirstName=user_record["FirstName"],
            LastName=user_record["LastName"],
        ),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("loginVerify:app", host="0.0.0.0", port=8000, reload=True)
