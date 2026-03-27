"""
Testcase repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, or_, func
from app.models.testcase import Testcase, TestcaseFlow, TestcaseInlineStep
from app.repositories.base import BaseRepository


class TestcaseRepository(BaseRepository[Testcase]):
    """Testcase repository"""

    def __init__(self, db: Session):
        super().__init__(Testcase, db)

    def get_by_name(self, name: str) -> Optional[Testcase]:
        """Get testcase by name"""
        return self.get_by_field('name', name)

    def get_with_flows(self, testcase_id: int) -> Optional[Testcase]:
        """Get testcase with all flows and steps loaded"""
        stmt = select(Testcase).options(
            joinedload(Testcase.testcase_flows),
            joinedload(Testcase.inline_steps),
            joinedload(Testcase.testcase_items),
            joinedload(Testcase.tags)
        ).where(Testcase.id == testcase_id)
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list_with_details(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        priority: Optional[List[str]] = None,
        tag_ids: Optional[List[int]] = None,
        project_id: Optional[int] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List testcases with details"""
        # Build query
        stmt = select(Testcase)

        # Apply filters
        filters = []
        if search:
            filters.append(Testcase.name.ilike(f'%{search}%'))
        if priority:
            filters.append(Testcase.priority.in_(priority))
        if project_id is not None:
            filters.append(Testcase.project_id == project_id)
        if tag_ids:
            from app.models.tag import testcase_tags
            stmt = stmt.join(testcase_tags, testcase_tags.c.testcase_id == Testcase.id)
            filters.append(testcase_tags.c.tag_id.in_(tag_ids))

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get total count
        count_stmt = select(func.count(func.distinct(Testcase.id))).select_from(Testcase)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        if tag_ids:
            from app.models.tag import testcase_tags
            count_stmt = count_stmt.join(testcase_tags, testcase_tags.c.testcase_id == Testcase.id)
        total = self.db.execute(count_stmt).scalar() or 0

        # Apply pagination and ordering
        # ✅ 使用joinedload一次性加载所有关联数据，避免N+1查询
        stmt = stmt.options(
            joinedload(Testcase.tags),
            joinedload(Testcase.testcase_flows),
            joinedload(Testcase.testcase_items),
            joinedload(Testcase.inline_steps)
        ).order_by(Testcase.created_at.desc()).offset(skip).limit(limit)

        # ✅ 一次性查询获取所有testcases及其关联数据
        testcases = self.db.execute(stmt).unique().scalars().all()

        # 构建结果
        results = []
        for testcase in testcases:
            # 计算流程数（从已加载的数据中获取）
            setup_flow_count = len([f for f in testcase.testcase_flows if f.flow_role == 'setup'])
            main_flow_count = len([f for f in testcase.testcase_flows if f.flow_role == 'main'])
            teardown_flow_count = len([f for f in testcase.testcase_flows if f.flow_role == 'teardown'])

            # 计算testcase_item_count（从已加载的数据中获取）
            testcase_item_count = len(testcase.testcase_items) if testcase.testcase_items else 0

            # ✅ 简化step_count计算（暂不统计复杂flow的步骤数）
            step_count = testcase_item_count  # 简化计算，避免嵌套查询

            results.append({
                'id': testcase.id,
                'name': testcase.name,
                'description': testcase.description,
                'priority': testcase.priority,
                'timeout': testcase.timeout,
                'params': testcase.params,
                'tags': [{'id': t.id, 'name': t.name} for t in testcase.tags],
                'setup_flow_count': setup_flow_count,
                'main_flow_count': main_flow_count,
                'teardown_flow_count': teardown_flow_count,
                'step_count': step_count,
                'testcase_item_count': testcase_item_count,
                'suite_count': self.check_suite_usage(testcase.id),
                'created_at': testcase.created_at,
                'updated_at': testcase.updated_at
            })

        return results, total

    def check_suite_usage(self, testcase_id: int) -> int:
        """Check how many suites use this testcase"""
        from app.models.suite import SuiteTestcase
        stmt = select(func.count(SuiteTestcase.id)).where(SuiteTestcase.testcase_id == testcase_id)
        return self.db.execute(stmt).scalar() or 0

    def create_with_flows(self, data: Dict[str, Any]) -> Testcase:
        """Create testcase with flows"""
        setup_flows = data.pop('setup_flows', [])
        main_flows = data.pop('main_flows', [])
        teardown_flows = data.pop('teardown_flows', [])
        inline_steps = data.pop('inline_steps', [])
        tag_ids = data.pop('tag_ids', None)

        testcase = Testcase(**data)
        self.db.add(testcase)
        self.db.flush()

        # Add flows
        for flow_data in setup_flows:
            tf = TestcaseFlow(
                testcase_id=testcase.id,
                flow_id=flow_data['flow_id'],
                flow_role='setup',
                order_index=flow_data['order'],
                enabled=flow_data.get('enabled', True),
                params=flow_data.get('params')
            )
            self.db.add(tf)

        for flow_data in main_flows:
            tf = TestcaseFlow(
                testcase_id=testcase.id,
                flow_id=flow_data['flow_id'],
                flow_role='main',
                order_index=flow_data['order'],
                enabled=flow_data.get('enabled', True),
                params=flow_data.get('params')
            )
            self.db.add(tf)

        for flow_data in teardown_flows:
            tf = TestcaseFlow(
                testcase_id=testcase.id,
                flow_id=flow_data['flow_id'],
                flow_role='teardown',
                order_index=flow_data['order'],
                enabled=flow_data.get('enabled', True),
                params=flow_data.get('params')
            )
            self.db.add(tf)

        # Add inline steps
        for step_data in inline_steps:
            tis = TestcaseInlineStep(
                testcase_id=testcase.id,
                step_id=step_data['step_id'],
                order_index=step_data['order'],
                override_value=step_data.get('override_value')
            )
            self.db.add(tis)

        # Add tags
        if tag_ids:
            from app.models.tag import Tag
            for tag_id in tag_ids:
                tag = self.db.get(Tag, tag_id)
                if tag:
                    testcase.tags.append(tag)

        self.db.commit()
        self.db.refresh(testcase)
        return testcase

    def update_with_flows(self, testcase_id: int, data: Dict[str, Any]) -> Optional[Testcase]:
        """Update testcase with flows"""
        testcase = self.get(testcase_id)
        if not testcase:
            return None

        # Update fields
        for field, value in data.items():
            if field not in ['setup_flows', 'main_flows', 'teardown_flows', 'inline_steps', 'tag_ids'] and hasattr(testcase, field):
                setattr(testcase, field, value)

        # Update flows if provided
        for role in ['setup_flows', 'main_flows', 'teardown_flows']:
            if role in data and data[role] is not None:
                # Delete existing flows for this role
                flow_role = role.replace('_flows', '')
                self.db.query(TestcaseFlow).filter(
                    and_(TestcaseFlow.testcase_id == testcase_id, TestcaseFlow.flow_role == flow_role)
                ).delete()

                # Add new flows
                for flow_data in data[role]:
                    tf = TestcaseFlow(
                        testcase_id=testcase_id,
                        flow_id=flow_data['flow_id'],
                        flow_role=flow_role,
                        order_index=flow_data['order'],
                        enabled=flow_data.get('enabled', True),
                        params=flow_data.get('params')
                    )
                    self.db.add(tf)

        # Update inline steps
        if 'inline_steps' in data and data['inline_steps'] is not None:
            self.db.query(TestcaseInlineStep).filter(TestcaseInlineStep.testcase_id == testcase_id).delete()
            for step_data in data['inline_steps']:
                tis = TestcaseInlineStep(
                    testcase_id=testcase_id,
                    step_id=step_data['step_id'],
                    order_index=step_data['order'],
                    override_value=step_data.get('override_value')
                )
                self.db.add(tis)

        # Update tags
        if 'tag_ids' in data:
            from app.models.tag import Tag
            testcase.tags.clear()
            if data['tag_ids'] is not None:
                for tag_id in data['tag_ids']:
                    tag = self.db.get(Tag, tag_id)
                    if tag:
                        testcase.tags.append(tag)

        self.db.commit()
        self.db.refresh(testcase)
        return testcase

    def duplicate(self, testcase_id: int, new_name: str) -> Optional[Testcase]:
        """Duplicate a testcase"""
        testcase = self.get_with_flows(testcase_id)
        if not testcase:
            return None

        # Create new testcase
        new_testcase = Testcase(
            name=new_name,
            description=testcase.description,
            priority=testcase.priority,
            timeout=testcase.timeout,
            params=testcase.params
        )
        self.db.add(new_testcase)
        self.db.flush()

        # Copy flows
        for tf in testcase.testcase_flows:
            new_tf = TestcaseFlow(
                testcase_id=new_testcase.id,
                flow_id=tf.flow_id,
                flow_role=tf.flow_role,
                order_index=tf.order_index,
                enabled=tf.enabled,
                params=tf.params
            )
            self.db.add(new_tf)

        # Copy inline steps
        for tis in testcase.inline_steps:
            new_tis = TestcaseInlineStep(
                testcase_id=new_testcase.id,
                step_id=tis.step_id,
                order_index=tis.order_index,
                override_value=tis.override_value
            )
            self.db.add(new_tis)

        # Copy tags
        for tag in testcase.tags:
            new_testcase.tags.append(tag)

        self.db.commit()
        self.db.refresh(new_testcase)
        return new_testcase
