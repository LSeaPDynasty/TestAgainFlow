"""
Suite repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from app.models.suite import Suite, SuiteTestcase
from app.repositories.base import BaseRepository


class SuiteRepository(BaseRepository[Suite]):
    """Suite repository"""

    def __init__(self, db: Session):
        super().__init__(Suite, db)

    def get_by_name(self, name: str) -> Optional[Suite]:
        """Get suite by name"""
        return self.get_by_field('name', name)

    def get_with_testcases(self, suite_id: int) -> Optional[Suite]:
        """Get suite with testcases loaded"""
        stmt = select(Suite).options(joinedload(Suite.suite_testcases)).where(Suite.id == suite_id)
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list_with_testcase_count(
        self,
        skip: int = 0,
        limit: int = 20,
        project_id: Optional[int] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List suites with testcase counts"""
        from app.models.flow import Flow, FlowStep
        from app.models.step import Step

        # 构建查询语句，先应用项目过滤
        query = select(Suite).order_by(Suite.created_at.desc())
        if project_id is not None:
            query = query.where(Suite.project_id == project_id)

        # 获取套件数据
        suites_data = []
        for suite in self.db.execute(query.offset(skip).limit(limit)).scalars():
            # 获取套件的用例数
            testcase_result = self.db.execute(
                select(func.count(SuiteTestcase.id))
                .where(SuiteTestcase.suite_id == suite.id)
            )
            testcase_count = testcase_result.scalar() or 0

            # 计算总步骤数
            total_step_count = 0

            # 获取套件的所有用例
            suite_testcases = self.db.execute(
                select(SuiteTestcase)
                .where(SuiteTestcase.suite_id == suite.id)
                .order_by(SuiteTestcase.order_index)
            ).scalars()

            for st in suite_testcases:
                # 获取用例的所有流程
                from app.models.testcase import TestcaseFlow
                testcase_flows = self.db.execute(
                    select(TestcaseFlow)
                    .where(TestcaseFlow.testcase_id == st.testcase_id)
                ).scalars()

                for tf in testcase_flows:
                    # 获取flow的步骤数
                    flow = self.db.execute(select(Flow).where(Flow.id == tf.flow_id)).scalar_one_or_none()
                    if flow and flow.flow_type == 'standard':
                        # 标准flow: 统计flow_steps
                        step_result = self.db.execute(
                            select(func.count(FlowStep.id))
                            .where(FlowStep.flow_id == tf.flow_id)
                        ).scalar()
                        total_step_count += step_result or 0

            suites_data.append({
                'id': suite.id,
                'name': suite.name,
                'description': suite.description,
                'priority': suite.priority,
                'enabled': suite.enabled,
                'testcase_count': testcase_count,
                'total_step_count': total_step_count,
                'created_at': suite.created_at,
                'updated_at': suite.updated_at
            })

        # 获取总数（带项目过滤）
        count_stmt = select(func.count(Suite.id))
        if project_id is not None:
            count_stmt = count_stmt.where(Suite.project_id == project_id)
        total = self.db.execute(count_stmt).scalar() or 0

        return suites_data, total

    def create_with_testcases(self, data: Dict[str, Any]) -> Suite:
        """Create suite with testcases"""
        testcases_data = data.pop('testcases', None)

        suite = Suite(**data)
        self.db.add(suite)
        self.db.flush()

        if testcases_data:
            for tc_data in testcases_data:
                st = SuiteTestcase(
                    suite_id=suite.id,
                    testcase_id=tc_data['testcase_id'],
                    order_index=tc_data['order'],
                    enabled=tc_data.get('enabled', True)
                )
                self.db.add(st)

        self.db.commit()
        self.db.refresh(suite)
        return suite

    def update_with_testcases(self, suite_id: int, data: Dict[str, Any]) -> Optional[Suite]:
        """Update suite with testcases"""
        suite = self.get(suite_id)
        if not suite:
            return None

        # Update fields
        for field, value in data.items():
            if field != 'testcases' and hasattr(suite, field):
                setattr(suite, field, value)

        # Update testcases if provided
        if 'testcases' in data:
            self.db.query(SuiteTestcase).filter(SuiteTestcase.suite_id == suite_id).delete()
            for tc_data in data['testcases']:
                st = SuiteTestcase(
                    suite_id=suite_id,
                    testcase_id=tc_data['testcase_id'],
                    order_index=tc_data['order'],
                    enabled=tc_data.get('enabled', True)
                )
                self.db.add(st)

        self.db.commit()
        self.db.refresh(suite)
        return suite

    def toggle_enabled(self, suite_id: int, enabled: bool) -> Optional[Suite]:
        """Toggle suite enabled state"""
        suite = self.get(suite_id)
        if suite:
            suite.enabled = enabled
            self.db.commit()
            self.db.refresh(suite)
        return suite
