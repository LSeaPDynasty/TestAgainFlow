"""
Screen repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from app.models.screen import Screen
from app.models.element import Element
from app.repositories.base import BaseRepository


class ScreenRepository(BaseRepository[Screen]):
    """Screen repository"""

    def __init__(self, db: Session):
        super().__init__(Screen, db)

    def get_by_name(self, name: str) -> Optional[Screen]:
        """Get screen by name"""
        return self.get_by_field('name', name)

    def get_with_elements(self, screen_id: int) -> Optional[Screen]:
        """Get screen with elements loaded"""
        stmt = select(Screen).options(joinedload(Screen.elements)).where(Screen.id == screen_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_element_count(self, screen_id: int) -> int:
        """Get element count for screen"""
        from app.models.element import Element
        stmt = select(func.count(Element.id)).where(Element.screen_id == screen_id)
        return self.db.execute(stmt).scalar() or 0

    def list_with_element_counts(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        project_id: Optional[int] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List screens with element counts"""
        # Build query
        stmt = select(
            Screen.id,
            Screen.name,
            Screen.activity,
            Screen.description,
            Screen.created_at,
            Screen.updated_at,
            func.count(Element.id).label('element_count')
        ).outerjoin(
            Element, Element.screen_id == Screen.id
        ).group_by(
            Screen.id,
            Screen.name,
            Screen.activity,
            Screen.description,
            Screen.created_at,
            Screen.updated_at
        )

        # Apply filters
        filters = []
        if search:
            filters.append(Screen.name.ilike(f'%{search}%'))
        if project_id is not None:
            filters.append(Screen.project_id == project_id)

        if filters:
            stmt = stmt.where(*filters)

        # Get total count (count distinct screens, not rows)
        count_stmt = select(func.count(func.distinct(Screen.id)))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = self.db.execute(count_stmt).scalar() or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(Screen.created_at.desc()).offset(skip).limit(limit)

        # Execute query
        results = []
        for row in self.db.execute(stmt):
            results.append({
                'id': row.id,
                'name': row.name,
                'activity': row.activity,
                'description': row.description,
                'created_at': row.created_at,
                'updated_at': row.updated_at,
                'element_count': row.element_count
            })

        return results, total

    def delete(self, id: int) -> bool:
        """Delete screen (cascade delete elements)"""
        screen = self.get(id)
        if not screen:
            return False

        # Element count check should be done at service layer
        self.db.delete(screen)
        self.db.commit()
        return True
