"""
Flow repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, func
from app.models.flow import Flow, FlowStep
from app.repositories.base import BaseRepository


class FlowRepository(BaseRepository[Flow]):
    """Flow repository"""

    def __init__(self, db: Session):
        super().__init__(Flow, db)

    def get_by_name(self, name: str) -> Optional[Flow]:
        """Get flow by name"""
        return self.get_by_field('name', name)

    def get_with_details(self, flow_id: int) -> Optional[Flow]:
        """Get flow with steps and tags loaded"""
        stmt = select(Flow).options(
            joinedload(Flow.flow_steps),
            joinedload(Flow.tags)
        ).where(Flow.id == flow_id)
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list_with_details(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        flow_type: Optional[str] = None,
        tag_ids: Optional[List[int]] = None,
        project_id: Optional[int] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List flows with step counts and tags"""
        # Build query using full entity to support joinedload
        stmt = select(Flow).outerjoin(
            FlowStep, FlowStep.flow_id == Flow.id
        )

        # Apply filters
        filters = []
        if search:
            filters.append(Flow.name.ilike(f'%{search}%'))
        if flow_type:
            filters.append(Flow.flow_type == flow_type)
        if project_id is not None:
            filters.append(Flow.project_id == project_id)
        if tag_ids:
            from app.models.tag import flow_tags
            stmt = stmt.join(flow_tags, flow_tags.c.flow_id == Flow.id)
            filters.append(flow_tags.c.tag_id.in_(tag_ids))

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get total count
        count_stmt = select(func.count(func.distinct(Flow.id))).select_from(Flow)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        if tag_ids:
            from app.models.tag import flow_tags
            count_stmt = count_stmt.join(flow_tags, flow_tags.c.flow_id == Flow.id)
        if flow_type:
            count_stmt = count_stmt.where(Flow.flow_type == flow_type)
        if project_id is not None:
            count_stmt = count_stmt.where(Flow.project_id == project_id)
        total = self.db.execute(count_stmt).scalar() or 0

        # Apply pagination and ordering with joinedload
        stmt = stmt.options(
            joinedload(Flow.tags)
        ).order_by(Flow.created_at.desc()).offset(skip).limit(limit)

        # Execute query with joinedload
        flows = self.db.execute(stmt).unique().scalars().all()

        # Build results with step count
        results = []
        for flow in flows:
            # Count steps for this flow
            step_count = len(flow.flow_steps) if flow.flow_steps else 0

            results.append({
                'id': flow.id,
                'name': flow.name,
                'description': flow.description,
                'flow_type': flow.flow_type,
                'requires': flow.requires or [],
                'step_count': step_count,
                'tags': [{'id': t.id, 'name': t.name} for t in flow.tags],
                'created_at': flow.created_at,
                'updated_at': flow.updated_at
            })

        return results, total

    def check_testcase_usage(self, flow_id: int) -> int:
        """Check how many testcases use this flow"""
        from app.models.testcase import TestcaseFlow
        stmt = select(func.count(TestcaseFlow.id)).where(TestcaseFlow.flow_id == flow_id)
        return self.db.execute(stmt).scalar() or 0

    def check_flow_call_usage(self, flow_id: int) -> List[Dict[str, Any]]:
        """Check which flows call this flow (via dsl_content)"""
        stmt = select(Flow.id, Flow.name).where(
            Flow.dsl_content.like(f'%call: %')
        )
        # This is a simplified check - in production, parse DSL properly
        results = self.db.execute(stmt).all()
        return [{'id': r.id, 'name': r.name} for r in results]

    def create_with_steps(self, data: Dict[str, Any]) -> Flow:
        """Create flow with steps"""
        steps_data = data.pop('steps', None)
        tag_ids = data.pop('tag_ids', None)

        flow = Flow(**data)
        self.db.add(flow)
        self.db.flush()

        # Add steps if provided
        if steps_data and data.get('flow_type') == 'standard':
            for step_data in steps_data:
                flow_step = FlowStep(
                    flow_id=flow.id,
                    step_id=step_data['step_id'],
                    order_index=step_data['order'],
                    override_value=step_data.get('override_value')
                )
                self.db.add(flow_step)

        # Add tags
        if tag_ids:
            from app.models.tag import Tag
            for tag_id in tag_ids:
                tag = self.db.get(Tag, tag_id)
                if tag:
                    flow.tags.append(tag)

        self.db.commit()
        self.db.refresh(flow)
        return flow

    def update_with_steps(self, flow_id: int, data: Dict[str, Any]) -> Optional[Flow]:
        """Update flow with steps"""
        flow = self.get(flow_id)
        if not flow:
            return None

        # Update flow fields
        for field, value in data.items():
            if field not in ['steps', 'tag_ids'] and hasattr(flow, field):
                setattr(flow, field, value)

        # Update steps if provided
        if 'steps' in data and data.get('flow_type') == 'standard':
            # Delete existing steps
            self.db.query(FlowStep).filter(FlowStep.flow_id == flow_id).delete()

            # Add new steps
            for step_data in data['steps']:
                # Convert Pydantic model to dict
                step_dict = step_data.model_dump() if hasattr(step_data, 'model_dump') else step_data
                flow_step = FlowStep(
                    flow_id=flow_id,
                    step_id=step_dict['step_id'],
                    order_index=step_dict['order'],
                    override_value=step_dict.get('override_value')
                )
                self.db.add(flow_step)

        # Update tags
        if 'tag_ids' in data:
            from app.models.tag import Tag
            flow.tags.clear()
            if data['tag_ids'] is not None:
                for tag_id in data['tag_ids']:
                    tag = self.db.get(Tag, tag_id)
                    if tag:
                        flow.tags.append(tag)

        self.db.commit()
        self.db.refresh(flow)
        return flow

    def duplicate(self, flow_id: int, new_name: str) -> Optional[Flow]:
        """Duplicate a flow"""
        flow = self.get_with_details(flow_id)
        if not flow:
            return None

        # Create new flow
        new_flow = Flow(
            name=new_name,
            description=flow.description,
            flow_type=flow.flow_type,
            requires=flow.requires,
            default_params=flow.default_params,
            dsl_content=flow.dsl_content,
            py_file=flow.py_file
        )
        self.db.add(new_flow)
        self.db.flush()

        # Copy steps
        for flow_step in flow.flow_steps:
            new_step = FlowStep(
                flow_id=new_flow.id,
                step_id=flow_step.step_id,
                order_index=flow_step.order_index,
                override_value=flow_step.override_value
            )
            self.db.add(new_step)

        # Copy tags
        for tag in flow.tags:
            new_flow.tags.append(tag)

        self.db.commit()
        self.db.refresh(new_flow)
        return new_flow
