"""Users/auth router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user_payload, get_db_session
from app.schemas.common import ApiResponse
from app.schemas.user import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.services.user_service import (
    ServiceValidationError,
    get_user_by_id,
    list_users,
    login_user,
    register_user,
)
from app.utils.response import error, ok

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=ApiResponse[UserResponse])
def register(req: UserRegisterRequest, db: Session = Depends(get_db_session)):
    response, validation_error = register_user(db, req)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message)
    return ok(data=response, message="User registered")


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(req: UserLoginRequest, db: Session = Depends(get_db_session)):
    response, validation_error = login_user(db, req)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message)
    return ok(data=response, message="Login success")


@router.get("/me", response_model=ApiResponse[UserResponse])
def me(
    db: Session = Depends(get_db_session),
    payload: dict | None = Depends(get_current_user_payload),
):
    if not payload:
        return error(code=4001, message="Unauthorized")
    user = get_user_by_id(db, int(payload["uid"]))
    if not user:
        return error(code=4004, message="User not found")
    return ok(data=user)


@router.get("", response_model=ApiResponse[list[UserResponse]])
def users(
    db: Session = Depends(get_db_session),
    payload: dict | None = Depends(get_current_user_payload),
):
    if not payload or payload.get("role") != "admin":
        return error(code=4001, message="Admin permission required")
    return ok(data=list_users(db))
