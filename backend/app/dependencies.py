"""
FastAPI dependencies
"""
from typing import Generator
from fastapi import Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.user_service import verify_token


def get_db_session() -> Generator[Session, None, None]:
    """Get database session"""
    yield from get_db()


def get_current_user_payload(authorization: str | None = Header(default=None)) -> dict | None:
    """Parse bearer token payload if provided and valid."""
    if not authorization:
        return None
    if not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return verify_token(token)
