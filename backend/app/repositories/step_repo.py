"""
Step repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, func
from app.models.step import Step
from app.models.screen import Screen
from app.models.element import Element
from app.repositories.base import BaseRepository


class StepRepository(BaseRepository[Step]):
    """Step repository"""

    def __init__(self, db: Session):
        super().__init__(Step, db)

    def get_with_details(self, step_id: int) -> Optional[Step]:
        """Get step with screen, element, and tags loaded"""
        stmt = select(Step).options(
            joinedload(Step.screen),
            joinedload(Step.element),
            joinedload(Step.tags)
        ).where(Step.id == step_id)
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list_by_screen(self, screen_id: int) -> List[Step]:
        """List steps by screen"""
        return self.list(filters={'screen_id': screen_id}, limit=1000)

    def list_by_action_type(self, action_type: str) -> List[Step]:
        """List steps by action type"""
        return self.list(filters={'action_type': action_type}, limit=1000)

    def list_with_details(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        screen_id: Optional[int] = None,
        action_type: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
        project_id: Optional[int] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List steps with screen and element info"""
        # Build query
        stmt = select(
            Step.id,
            Step.name,
            Step.description,
            Step.screen_id,
            Screen.name.label('screen_name'),
            Step.action_type,
            Step.element_id,
            Element.name.label('element_name'),
            Step.action_value,
            Step.assert_config,
            Step.wait_after_ms,
            Step.continue_on_error,
            Step.created_at,
            Step.updated_at
        ).outerjoin(
            Screen, Screen.id == Step.screen_id
        ).outerjoin(
            Element, Element.id == Step.element_id
        )

        # Apply filters
        filters = []
        if search:
            filters.append(Step.name.ilike(f'%{search}%'))
        if screen_id:
            filters.append(Step.screen_id == screen_id)
        if action_type:
            filters.append(Step.action_type == action_type)
        if project_id is not None:
            filters.append(Step.project_id == project_id)
        if tag_ids:
            from app.models.tag import step_tags
            stmt = stmt.join(step_tags, step_tags.c.step_id == Step.id)
            filters.append(step_tags.c.tag_id.in_(tag_ids))

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get total count
        count_stmt = select(func.count(func.distinct(Step.id))).select_from(Step)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        if tag_ids:
            from app.models.tag import step_tags
            count_stmt = count_stmt.join(step_tags, step_tags.c.step_id == Step.id)
        if project_id is not None:
            count_stmt = count_stmt.where(Step.project_id == project_id)
        total = self.db.execute(count_stmt).scalar() or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(Step.created_at.desc()).offset(skip).limit(limit)

        # ✅ 执行查询（部分字段查询，不能使用joinedload）
        results = []
        for row in self.db.execute(stmt):
            # ✅ 单独查询tags（但只查询有tags的step，减少查询次数）
            tags = []
            # 简化：不在列表查询时加载tags，避免N+1

            results.append({
                'id': row.id,
                'name': row.name,
                'description': row.description,
                'screen_id': row.screen_id,
                'screen_name': row.screen_name,
                'action_type': row.action_type,
                'element_id': row.element_id,
                'element_name': row.element_name,
                'action_value': row.action_value,  # 可能是None
                'assert_config': row.assert_config,  # 可能是None
                'wait_after_ms': row.wait_after_ms or 0,
                'continue_on_error': bool(row.continue_on_error) if row.continue_on_error is not None else False,
                'tags': tags,
                'created_at': row.created_at,
                'updated_at': row.updated_at
            })

        return results, total

    def check_flow_usage(self, step_id: int) -> int:
        """Check how many flows use this step"""
        from app.models.flow import FlowStep
        stmt = select(func.count(FlowStep.id)).where(FlowStep.step_id == step_id)
        return self.db.execute(stmt).scalar() or 0

    def add_tags(self, step_id: int, tag_ids: List[int]) -> None:
        """Add tags to step"""
        step = self.get(step_id)
        if step:
            from app.models.tag import Tag
            for tag_id in tag_ids:
                tag = self.db.get(Tag, tag_id)
                if tag and tag not in step.tags:
                    step.tags.append(tag)
            self.db.commit()

    def set_tags(self, step_id: int, tag_ids: List[int]) -> None:
        """Set tags for step (replace existing)"""
        step = self.get_with_details(step_id)
        if step:
            from app.models.tag import Tag
            step.tags.clear()
            if tag_ids is not None:
                for tag_id in tag_ids:
                    tag = self.db.get(Tag, tag_id)
                    if tag:
                        step.tags.append(tag)
            self.db.commit()
