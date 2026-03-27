"""Data store router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse
from app.schemas.data_store import DataStoreEnvUpdate, DataStoreResponse
from app.services.data_store_service import (
    delete_env_data,
    get_all_data,
    get_env_data,
    update_env_data,
)
from app.utils.response import ok

router = APIRouter(prefix="/data-store", tags=["data-store"])


@router.get("", response_model=ApiResponse[DataStoreResponse])
def get_all_data_endpoint(db: Session = Depends(get_db_session)):
    """Get all environment data."""
    return ok(data=get_all_data(db))


@router.get("/{env:path}", response_model=ApiResponse[dict])
def get_env_data_endpoint(env: str, db: Session = Depends(get_db_session)):
    """Get specific environment data."""
    return ok(data=get_env_data(db, env))


@router.put("/{env:path}", response_model=ApiResponse)
def update_env_data_endpoint(env: str, req: DataStoreEnvUpdate, db: Session = Depends(get_db_session)):
    """Update environment data."""
    update_env_data(db, env, req.data)
    return ok(message=f"Environment '{env}' data updated successfully")


@router.delete("/{env:path}", response_model=ApiResponse)
def delete_env_endpoint(env: str, db: Session = Depends(get_db_session)):
    """Delete environment."""
    if not delete_env_data(db, env):
        return ok(message=f"Environment '{env}' not found", data=None)
    return ok(message=f"Environment '{env}' deleted successfully")
