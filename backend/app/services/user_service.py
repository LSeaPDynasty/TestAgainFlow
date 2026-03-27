"""User and auth service."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.repositories.user_repo import UserRepository
from app.schemas.user import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse


@dataclass
class ServiceValidationError:
    code: int
    message: str


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt_value}:{password}".encode("utf-8")).hexdigest()
    return f"{salt_value}${digest}"


def _verify_password(password: str, stored: str) -> bool:
    if "$" not in stored:
        return False
    salt, expected = stored.split("$", 1)
    candidate = _hash_password(password, salt=salt).split("$", 1)[1]
    return hmac.compare_digest(candidate, expected)


def _sign(data: str) -> str:
    sig = hmac.new(settings.auth_secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")


def _encode(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _decode(segment: str) -> dict:
    padded = segment + "=" * (-len(segment) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
    return json.loads(raw.decode("utf-8"))


def issue_token(user_id: int, username: str, role: str) -> tuple[str, int]:
    expires_at = int(time.time()) + int(settings.auth_token_ttl_seconds)
    payload = {"uid": user_id, "usr": username, "role": role, "exp": expires_at}
    body = _encode(payload)
    signature = _sign(body)
    return f"{body}.{signature}", int(settings.auth_token_ttl_seconds)


def verify_token(token: str) -> Optional[dict]:
    try:
        body, signature = token.split(".", 1)
        if not hmac.compare_digest(_sign(body), signature):
            return None
        payload = _decode(body)
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def register_user(db: Session, req: UserRegisterRequest) -> tuple[Optional[UserResponse], Optional[ServiceValidationError]]:
    repo = UserRepository(db)
    if repo.get_by_username(req.username):
        return None, ServiceValidationError(code=4009, message="Username already exists")
    if req.email and repo.get_by_email(req.email):
        return None, ServiceValidationError(code=4009, message="Email already exists")

    user = repo.create(
        {
            "username": req.username,
            "email": req.email,
            "password_hash": _hash_password(req.password),
            "role": req.role,
            "is_active": True,
        }
    )
    return UserResponse.model_validate(user), None


def login_user(db: Session, req: UserLoginRequest) -> tuple[Optional[TokenResponse], Optional[ServiceValidationError]]:
    repo = UserRepository(db)
    user = repo.get_by_username(req.username)
    if not user or not _verify_password(req.password, user.password_hash):
        return None, ServiceValidationError(code=4001, message="Invalid username or password")
    if not user.is_active:
        return None, ServiceValidationError(code=4001, message="User is inactive")

    token, expires_in = issue_token(user.id, user.username, user.role)
    return (
        TokenResponse(
            access_token=token,
            expires_in=expires_in,
            user=UserResponse.model_validate(user),
        ),
        None,
    )


def get_user_by_id(db: Session, user_id: int) -> Optional[UserResponse]:
    repo = UserRepository(db)
    user = repo.get(user_id)
    return UserResponse.model_validate(user) if user else None


def list_users(db: Session):
    repo = UserRepository(db)
    users = repo.list(limit=1000)
    return [UserResponse.model_validate(u) for u in users]
