"""
DataStore repository
"""
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.data_store import DataStore
from app.repositories.base import BaseRepository


class DataStoreRepository(BaseRepository[DataStore]):
    """DataStore repository"""

    def __init__(self, db: Session):
        super().__init__(DataStore, db)

    def get_by_env(self, env: str) -> List[DataStore]:
        """Get all data for an environment"""
        stmt = select(DataStore).where(DataStore.env == env)
        return list(self.db.execute(stmt).scalars().all())

    def get_env_as_dict(self, env: str) -> Dict[str, str]:
        """Get environment data as dict"""
        records = self.get_by_env(env)
        return {r.key_name: r.value for r in records}

    def get_all_envs(self) -> List[str]:
        """Get all environment names"""
        stmt = select(DataStore.env).distinct()
        return [r[0] for r in self.db.execute(stmt)]

    def get_all_data(self) -> Dict[str, Dict[str, str]]:
        """Get all data grouped by environment"""
        envs = self.get_all_envs()
        result = {}
        for env in envs:
            result[env] = self.get_env_as_dict(env)
        return result

    def upsert_env_data(self, env: str, data: Dict[str, str]) -> None:
        """Upsert data for an environment"""
        # Clear existing data for env
        self.db.query(DataStore).filter(DataStore.env == env).delete()

        # Insert new data
        for key, value in data.items():
            if value is not None:  # Skip None values (delete)
                record = DataStore(env=env, key_name=key, value=value)
                self.db.add(record)

        self.db.commit()

    def delete_env(self, env: str) -> bool:
        """Delete all data for an environment"""
        stmt = select(DataStore).where(DataStore.env == env)
        exists = self.db.execute(stmt).first() is not None
        if exists:
            self.db.query(DataStore).filter(DataStore.env == env).delete()
            self.db.commit()
        return exists
