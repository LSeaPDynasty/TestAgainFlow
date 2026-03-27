"""
TestPlan repository - data access layer for test plans
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from app.models.test_plan import TestPlan, TestPlanSuite, TestPlanTestcaseOrder
from app.repositories.base import BaseRepository


class TestPlanRepository(BaseRepository[TestPlan]):
    """TestPlan repository"""

    def __init__(self, db: Session):
        super().__init__(TestPlan, db)

    def get_by_name(self, name: str) -> Optional[TestPlan]:
        """Get test plan by name"""
        return self.get_by_field('name', name)

    def get_with_details(self, plan_id: int) -> Optional[TestPlan]:
        """Get test plan with suites and testcase orders loaded"""
        stmt = (
            select(TestPlan)
            .options(
                joinedload(TestPlan.test_plan_suites)
                .joinedload(TestPlanSuite.suite)
            )
            .where(TestPlan.id == plan_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_project(self, project_id: int, skip: int = 0, limit: int = 20) -> tuple[List[Dict[str, Any]], int]:
        """List test plans by project with suite counts"""
        query = select(TestPlan).where(TestPlan.project_id == project_id)

        # Get total count
        count_stmt = select(func.count(TestPlan.id)).where(TestPlan.project_id == project_id)
        total = self.db.execute(count_stmt).scalar() or 0

        # Get test plans with suite counts
        plans_data = []
        for plan in self.db.execute(query.offset(skip).limit(limit)).scalars():
            # Get suite count
            suite_result = self.db.execute(
                select(func.count(TestPlanSuite.id))
                .where(TestPlanSuite.test_plan_id == plan.id)
            )
            suite_count = suite_result.scalar() or 0

            plans_data.append({
                'id': plan.id,
                'name': plan.name,
                'description': plan.description,
                'execution_strategy': plan.execution_strategy,
                'max_parallel_tasks': plan.max_parallel_tasks,
                'enabled': plan.enabled,
                'project_id': plan.project_id,
                'suite_count': suite_count,
                'created_at': plan.created_at,
                'updated_at': plan.updated_at
            })

        return plans_data, total

    def create_with_suites(self, data: Dict[str, Any]) -> TestPlan:
        """Create test plan with suites"""
        suites_data = data.pop('suites', None)

        plan = TestPlan(**data)
        self.db.add(plan)
        self.db.flush()

        if suites_data:
            for suite_data in suites_data:
                tps = TestPlanSuite(
                    test_plan_id=plan.id,
                    suite_id=suite_data['suite_id'],
                    order_index=suite_data['order'],
                    enabled=suite_data.get('enabled', True)
                )
                self.db.add(tps)

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def update_with_suites(self, plan_id: int, data: Dict[str, Any]) -> Optional[TestPlan]:
        """Update test plan with suites"""
        plan = self.get(plan_id)
        if not plan:
            return None

        # Update fields
        for field, value in data.items():
            if field != 'suites' and hasattr(plan, field):
                setattr(plan, field, value)

        # Update suites if provided
        if 'suites' in data:
            # Delete existing suites
            self.db.query(TestPlanSuite).filter(TestPlanSuite.test_plan_id == plan_id).delete()

            # Add new suites
            for suite_data in data['suites']:
                tps = TestPlanSuite(
                    test_plan_id=plan_id,
                    suite_id=suite_data['suite_id'],
                    order_index=suite_data['order'],
                    enabled=suite_data.get('enabled', True)
                )
                self.db.add(tps)

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def add_suite_to_plan(self, plan_id: int, suite_id: int, order_index: int, enabled: bool = True) -> Optional[TestPlanSuite]:
        """Add a suite to test plan"""
        # Check if already exists
        existing = self.db.execute(
            select(TestPlanSuite).where(
                TestPlanSuite.test_plan_id == plan_id,
                TestPlanSuite.suite_id == suite_id
            )
        ).scalar_one_or_none()

        if existing:
            return existing

        tps = TestPlanSuite(
            test_plan_id=plan_id,
            suite_id=suite_id,
            order_index=order_index,
            enabled=enabled
        )
        self.db.add(tps)
        self.db.commit()
        self.db.refresh(tps)
        return tps

    def remove_suite_from_plan(self, plan_id: int, suite_id: int) -> bool:
        """Remove a suite from test plan"""
        tps = self.db.execute(
            select(TestPlanSuite).where(
                TestPlanSuite.test_plan_id == plan_id,
                TestPlanSuite.suite_id == suite_id
            )
        ).scalar_one_or_none()

        if not tps:
            return False

        self.db.delete(tps)
        self.db.commit()
        return True

    def reorder_suites(self, plan_id: int, suite_orders: List[Dict[str, Any]]) -> bool:
        """Reorder suites in test plan"""
        for item in suite_orders:
            suite_id = item.get('suite_id')
            order_index = item.get('order_index')

            tps = self.db.execute(
                select(TestPlanSuite).where(
                    TestPlanSuite.test_plan_id == plan_id,
                    TestPlanSuite.suite_id == suite_id
                )
            ).scalar_one_or_none()

            if tps:
                tps.order_index = order_index

        self.db.commit()
        return True

    def set_testcase_order(self, test_plan_suite_id: int, testcase_orders: List[Dict[str, Any]]) -> bool:
        """Set testcase order for a specific test plan suite"""
        # Delete existing orders
        self.db.query(TestPlanTestcaseOrder).filter(
            TestPlanTestcaseOrder.test_plan_suite_id == test_plan_suite_id
        ).delete()

        # Add new orders
        for item in testcase_orders:
            testcase_id = item.get('testcase_id')
            order_index = item.get('order_index')

            tpto = TestPlanTestcaseOrder(
                test_plan_suite_id=test_plan_suite_id,
                testcase_id=testcase_id,
                order_index=order_index
            )
            self.db.add(tpto)

        self.db.commit()
        return True

    def get_testcase_orders(self, test_plan_suite_id: int) -> List[TestPlanTestcaseOrder]:
        """Get testcase orders for a specific test plan suite"""
        stmt = (
            select(TestPlanTestcaseOrder)
            .where(TestPlanTestcaseOrder.test_plan_suite_id == test_plan_suite_id)
            .order_by(TestPlanTestcaseOrder.order_index)
        )
        return list(self.db.execute(stmt).scalars().all())

    def toggle_enabled(self, plan_id: int, enabled: bool) -> Optional[TestPlan]:
        """Toggle test plan enabled state"""
        plan = self.get(plan_id)
        if plan:
            plan.enabled = enabled
            self.db.commit()
            self.db.refresh(plan)
        return plan

    def get_suite_with_ordered_testcases(self, test_plan_suite_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a test plan suite with testcases in custom order or default order
        Returns suite info and ordered testcases
        """
        tps = self.db.get(TestPlanSuite, test_plan_suite_id)
        if not tps:
            return None

        # Get custom orders if they exist
        custom_orders = self.get_testcase_orders(test_plan_suite_id)

        if custom_orders:
            # Use custom order
            testcase_ids = [order.testcase_id for order in custom_orders]
            testcase_order_map = {order.testcase_id: order.order_index for order in custom_orders}
        else:
            # Use default suite order
            from app.models.suite import SuiteTestcase
            suite_testcases = self.db.execute(
                select(SuiteTestcase)
                .where(SuiteTestcase.suite_id == tps.suite_id)
                .order_by(SuiteTestcase.order_index)
            ).scalars().all()

            testcase_ids = [st.testcase_id for st in suite_testcases]
            testcase_order_map = {st.testcase_id: st.order_index for st in suite_testcases}

        # Get testcase details
        from app.models.testcase import Testcase
        testcases = []
        for tc_id in testcase_ids:
            tc = self.db.get(Testcase, tc_id)
            if tc:
                testcases.append({
                    'testcase_id': tc.id,
                    'testcase_name': tc.name,
                    'priority': tc.priority,
                    'order_index': testcase_order_map.get(tc_id, 0)
                })

        return {
            'id': tps.id,
            'test_plan_id': tps.test_plan_id,
            'suite_id': tps.suite_id,
            'order_index': tps.order_index,
            'enabled': tps.enabled,
            'execution_config': tps.execution_config,
            'testcases': testcases
        }
