"""Service helpers for data store endpoints."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.data_store_repo import DataStoreRepository


def get_all_data(db: Session):
    return DataStoreRepository(db).get_all_data()


def get_env_data(db: Session, env: str):
    return DataStoreRepository(db).get_env_as_dict(env)


def update_env_data(db: Session, env: str, data: dict):
    DataStoreRepository(db).upsert_env_data(env, data)


def delete_env_data(db: Session, env: str) -> bool:
    return DataStoreRepository(db).delete_env(env)
