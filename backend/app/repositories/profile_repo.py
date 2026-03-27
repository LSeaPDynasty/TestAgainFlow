"""
Profile repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.models.profile import Profile
from app.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    """Profile repository"""

    def __init__(self, db: Session):
        super().__init__(Profile, db)

    def get_by_name(self, name: str) -> Optional[Profile]:
        """Get profile by name"""
        return self.get_by_field('name', name)

    def get_with_variables(self, profile_id: int) -> Optional[Profile]:
        """Get profile with tags loaded"""
        stmt = select(Profile).options(joinedload(Profile.tags)).where(Profile.id == profile_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_with_details(
        self,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """List profiles with variable counts"""
        stmt = select(Profile).order_by(Profile.created_at.desc()).offset(skip).limit(limit)
        total = self.count()

        results = []
        for profile in self.db.execute(stmt).scalars():
            vars_dict = profile.variables or {}
            results.append({
                'id': profile.id,
                'name': profile.name,
                'description': profile.description,
                'variable_count': len(vars_dict),
                'tags': [{'id': t.id, 'name': t.name} for t in profile.tags],
                'created_at': profile.created_at,
                'updated_at': profile.updated_at
            })

        return results, total
