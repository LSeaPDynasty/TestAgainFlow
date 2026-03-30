"""
FastAPI dependencies
"""
from typing import Generator
from fastapi import Depends, Header, HTTPException, status
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


def require_auth(payload: dict | None = Depends(get_current_user_payload)) -> dict:
    """Require valid authentication, raise 401 if not authenticated."""
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_admin(payload: dict = Depends(require_auth)) -> dict:
    """Require admin role, raise 403 if not admin."""
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required",
        )
    return payload
