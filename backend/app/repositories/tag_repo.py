"""
Tag repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.tag import Tag, step_tags, flow_tags, testcase_tags
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    """Tag repository"""

    def __init__(self, db: Session):
        super().__init__(Tag, db)

    def get_by_name(self, name: str) -> Optional[Tag]:
        """Get tag by name"""
        return self.get_by_field('name', name)

    def list_with_usage_count(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Dict[str, Any]], int]:
        """List tags with usage count"""
        # Count usage across all tables
        stmt = select(
            Tag.id,
            Tag.name,
            Tag.color,
            Tag.created_at,
            func.coalesce(
                select(func.count(step_tags.c.step_id)).where(step_tags.c.tag_id == Tag.id),
                0
            ) +
            func.coalesce(
                select(func.count(flow_tags.c.flow_id)).where(flow_tags.c.tag_id == Tag.id),
                0
            ) +
            func.coalesce(
                select(func.count(testcase_tags.c.testcase_id)).where(testcase_tags.c.tag_id == Tag.id),
                0
            ).label('usage_count')
        ).order_by(
            Tag.created_at.desc()
        ).offset(skip).limit(limit)

        total = self.count()

        results = []
        for row in self.db.execute(stmt):
            results.append({
                'id': row.id,
                'name': row.name,
                'color': row.color,
                'usage_count': row.usage_count or 0,
                'created_at': row.created_at
            })

        return results, total
