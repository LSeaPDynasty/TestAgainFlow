"""Service helpers for test plan endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.repositories.test_plan_repo import TestPlanRepository
from app.repositories.suite_repo import SuiteRepository
from app.repositories.testcase_repo import TestcaseRepository
from app.repositories.run_history_repo import RunHistoryRepository
from app.repositories.device_repo import DeviceRepository
from app.repositories.profile_repo import ProfileRepository
from app.schemas.run import RunCreate, RunResponse
from app.services.run_service import start_run
from app.services.platform_capability_service import normalize_platform, get_platform_supported_actions, collect_actions_for_suites
from app.models.suite import Suite


@dataclass
class ServiceValidationError:
    code: int
    message: str
    data: Optional[dict] = None


def list_test_plans(
    db: Session,
    *,
    skip: int,
    limit: int,
    project_id: Optional[int] = None,
):
    """List test plans with optional project filter"""
    repo = TestPlanRepository(db)

    if project_id is not None:
        return repo.get_by_project(project_id, skip=skip, limit=limit)

    # List all without project filter
    plans = repo.list(skip=skip, limit=limit, order_by='created_at', order='desc')
    total = repo.count()

    # Add suite counts
    plans_data = []
    for plan in plans:
        from app.models.test_plan import TestPlanSuite
        suite_result = db.execute(
            select(func.count(TestPlanSuite.id)).where(TestPlanSuite.test_plan_id == plan.id)
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


def get_test_plan_detail(db: Session, plan_id: int) -> Optional[Dict[str, Any]]:
    """Get test plan with all details including suites and testcases"""
    repo = TestPlanRepository(db)
    plan = repo.get_with_details(plan_id)
    if not plan:
        return None

    suites_data = []
    for tps in plan.test_plan_suites:
        suite_info = repo.get_suite_with_ordered_testcases(tps.id)
        if suite_info:
            suites_data.append(suite_info)

    return {
        'id': plan.id,
        'name': plan.name,
        'description': plan.description,
        'execution_strategy': plan.execution_strategy,
        'max_parallel_tasks': plan.max_parallel_tasks,
        'enabled': plan.enabled,
        'project_id': plan.project_id,
        'suites': suites_data,
        'created_at': plan.created_at,
        'updated_at': plan.updated_at
    }


def create_test_plan(
    db: Session,
    name: str,
    description: Optional[str],
    execution_strategy: str,
    max_parallel_tasks: int,
    project_id: Optional[int],
    suites: Optional[List[Dict[str, Any]]]
) -> tuple[Optional[Dict[str, Any]], Optional[ServiceValidationError]]:
    """Create a test plan with suites"""
    repo = TestPlanRepository(db)
    suite_repo = SuiteRepository(db)

    if repo.get_by_name(name):
        return None, ServiceValidationError(code=4009, message="Test plan name already exists")

    # Validate suites if provided
    if suites:
        for suite_data in suites:
            suite = suite_repo.get(suite_data.get('suite_id'))
            if not suite:
                return None, ServiceValidationError(
                    code=4004,
                    message=f"Suite not found: id={suite_data.get('suite_id')}",
                )

    plan_data = {
        'name': name,
        'description': description,
        'execution_strategy': execution_strategy,
        'max_parallel_tasks': max_parallel_tasks,
        'project_id': project_id,
        'suites': suites
    }

    plan = repo.create_with_suites(plan_data)
    return build_test_plan_response(db, plan), None


def update_test_plan(
    db: Session,
    plan_id: int,
    name: Optional[str],
    description: Optional[str],
    execution_strategy: Optional[str],
    max_parallel_tasks: Optional[int],
    suites: Optional[List[Dict[str, Any]]]
) -> tuple[Optional[Dict[str, Any]], Optional[ServiceValidationError]]:
    """Update a test plan"""
    repo = TestPlanRepository(db)
    suite_repo = SuiteRepository(db)

    plan = repo.get(plan_id)
    if not plan:
        return None, ServiceValidationError(code=4004, message=f"Test plan not found: id={plan_id}")

    if name and name != plan.name and repo.get_by_name(name):
        return None, ServiceValidationError(code=4009, message="Test plan name already exists")

    # Validate suites if provided
    if suites:
        for suite_data in suites:
            suite = suite_repo.get(suite_data.get('suite_id'))
            if not suite:
                return None, ServiceValidationError(
                    code=4004,
                    message=f"Suite not found: id={suite_data.get('suite_id')}",
                )

    update_data = {}
    if name is not None:
        update_data['name'] = name
    if description is not None:
        update_data['description'] = description
    if execution_strategy is not None:
        update_data['execution_strategy'] = execution_strategy
    if max_parallel_tasks is not None:
        update_data['max_parallel_tasks'] = max_parallel_tasks
    if suites is not None:
        update_data['suites'] = suites

    updated = repo.update_with_suites(plan_id, update_data)
    return build_test_plan_response(db, updated), None


def delete_test_plan(db: Session, plan_id: int) -> Optional[ServiceValidationError]:
    """Delete a test plan"""
    repo = TestPlanRepository(db)
    if not repo.delete(plan_id):
        return ServiceValidationError(code=4004, message=f"Test plan not found: id={plan_id}")
    return None


def toggle_test_plan(
    db: Session,
    plan_id: int,
    enabled: bool
) -> tuple[Optional[Dict[str, Any]], Optional[ServiceValidationError]]:
    """Toggle test plan enabled state"""
    repo = TestPlanRepository(db)
    plan = repo.toggle_enabled(plan_id, enabled)
    if not plan:
        return None, ServiceValidationError(code=4004, message=f"Test plan not found: id={plan_id}")
    return build_test_plan_response(db, plan), None


def add_suites_to_plan(
    db: Session,
    plan_id: int,
    suite_ids: List[int]
) -> tuple[Optional[Dict[str, Any]], Optional[ServiceValidationError]]:
    """Add suites to test plan"""
    repo = TestPlanRepository(db)
    suite_repo = SuiteRepository(db)

    plan = repo.get(plan_id)
    if not plan:
        return None, ServiceValidationError(code=4004, message=f"Test plan not found: id={plan_id}")

    # Get current max order
    from app.models.test_plan import TestPlanSuite
    from sqlalchemy import select
    current_max = db.execute(
        select(func.coalesce(func.max(TestPlanSuite.order_index), 0))
        .where(TestPlanSuite.test_plan_id == plan_id)
    ).scalar() or 0

    # Add suites
    for suite_id in suite_ids:
        suite = suite_repo.get(suite_id)
        if not suite:
            return None, ServiceValidationError(
                code=4004,
                message=f"Suite not found: id={suite_id}",
            )

        current_max += 1
        repo.add_suite_to_plan(plan_id, suite_id, current_max)

    # Refresh and return
    updated_plan = repo.get_with_details(plan_id)
    return build_test_plan_response(db, updated_plan), None


def remove_suites_from_plan(
    db: Session,
    plan_id: int,
    suite_ids: List[int]
) -> tuple[Optional[Dict[str, Any]], Optional[ServiceValidationError]]:
    """Remove suites from test plan"""
    repo = TestPlanRepository(db)

    plan = repo.get(plan_id)
    if not plan:
        return None, ServiceValidationError(code=4004, message=f"Test plan not found: id={plan_id}")

    for suite_id in suite_ids:
        repo.remove_suite_from_plan(plan_id, suite_id)

    # Refresh and return
    updated_plan = repo.get_with_details(plan_id)
    return build_test_plan_response(db, updated_plan), None


def reorder_plan_suites(
    db: Session,
    plan_id: int,
    suite_orders: List[Dict[str, Any]]
) -> tuple[Optional[Dict[str, Any]], Optional[ServiceValidationError]]:
    """Reorder suites in test plan"""
    repo = TestPlanRepository(db)

    plan = repo.get(plan_id)
    if not plan:
        return None, ServiceValidationError(code=4004, message=f"Test plan not found: id={plan_id}")

    repo.reorder_suites(plan_id, suite_orders)

    # Refresh and return
    updated_plan = repo.get_with_details(plan_id)
    return build_test_plan_response(db, updated_plan), None


def set_suite_testcase_order(
    db: Session,
    plan_id: int,
    suite_id: int,
    testcase_orders: List[Dict[str, Any]]
) -> tuple[Optional[Dict[str, Any]], Optional[ServiceValidationError]]:
    """Set testcase order for a specific suite in test plan"""
    repo = TestPlanRepository(db)

    # Find the test plan suite
    from app.models.test_plan import TestPlanSuite
    from sqlalchemy import select
    tps = db.execute(
        select(TestPlanSuite).where(
            TestPlanSuite.test_plan_id == plan_id,
            TestPlanSuite.suite_id == suite_id
        )
    ).scalar_one_or_none()

    if not tps:
        return None, ServiceValidationError(
            code=4004,
            message=f"Suite not found in test plan: plan_id={plan_id}, suite_id={suite_id}"
        )

    # Validate testcases
    tc_repo = TestcaseRepository(db)
    for item in testcase_orders:
        tc = tc_repo.get(item.get('testcase_id'))
        if not tc:
            return None, ServiceValidationError(
                code=4004,
                message=f"Testcase not found: id={item.get('testcase_id')}"
            )

    repo.set_testcase_order(tps.id, testcase_orders)

    # Refresh and return
    updated_plan = repo.get_with_details(plan_id)
    return build_test_plan_response(db, updated_plan), None


def execute_test_plan(
    db: Session,
    plan_id: int,
    platform: str,
    device_serial: Optional[str],
    profile_id: Optional[int],
    timeout: Optional[int],
    extra_args: Optional[Dict[str, Any]],
    priority: Optional[str]
) -> tuple[Optional[List[RunResponse]], Optional[ServiceValidationError]]:
    """Execute a test plan"""
    repo = TestPlanRepository(db)
    history_repo = RunHistoryRepository(db)

    plan = repo.get_with_details(plan_id)
    if not plan:
        return None, ServiceValidationError(code=4004, message=f"Test plan not found: id={plan_id}")

    if not plan.enabled:
        return None, ServiceValidationError(code=4001, message="Test plan is disabled")

    if not plan.test_plan_suites:
        return None, ServiceValidationError(code=4001, message="Test plan has no suites")

    # Filter enabled suites and sort by order
    enabled_suites = [tps for tps in plan.test_plan_suites if tps.enabled]
    enabled_suites.sort(key=lambda x: x.order_index)

    if not enabled_suites:
        return None, ServiceValidationError(code=4001, message="Test plan has no enabled suites")

    # Generate task_id for the test plan
    task_id = f"plan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    # Create parent run_history record for the test plan
    total_testcase_count = 0
    for tps in enabled_suites:
        from app.models.suite import SuiteTestcase
        testcase_count = db.execute(
            select(func.count(SuiteTestcase.id))
            .where(SuiteTestcase.suite_id == tps.suite_id)
            .where(SuiteTestcase.enabled == True)
        ).scalar() or 0
        total_testcase_count += testcase_count

    # Get device name if device_serial provided
    device_name = None
    if device_serial:
        device_repo = DeviceRepository(db)
        device = device_repo.get_by_serial(device_serial)
        if device:
            device_name = device.name

    # Get profile name if profile_id provided
    profile_name = None
    if profile_id:
        profile_repo = ProfileRepository(db)
        profile = profile_repo.get(profile_id)
        if profile:
            profile_name = profile.name

    plan_history_data = {
        "task_id": task_id,
        "type": "test_plan",
        "target_id": plan.id,
        "target_name": plan.name,
        "result": "pending",
        "profile_id": profile_id,
        "profile_name": profile_name,
        "device_serial": device_serial,
        "device_name": device_name,
        "started_at": datetime.utcnow(),
        "total_count": total_testcase_count,
        "success_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "test_plan_id": plan_id,
    }
    history_repo.create(plan_history_data)

    # Convert string priority to integer
    priority_map = {
        'low': 5,
        'normal': 7,
        'high': 9,
    }
    int_priority = priority_map.get(priority or 'normal', 7)

    # Execute based on strategy
    if plan.execution_strategy == 'sequential':
        return _execute_sequential(
            db,
            plan,
            enabled_suites,
            platform,
            device_serial,
            profile_id,
            timeout,
            extra_args,
            int_priority,
            task_id
        )
    elif plan.execution_strategy == 'parallel':
        return _execute_parallel(
            db,
            plan,
            enabled_suites,
            platform,
            device_serial,
            profile_id,
            timeout,
            extra_args,
            int_priority,
            task_id
        )
    else:
        return None, ServiceValidationError(code=4001, message=f"Invalid execution strategy: {plan.execution_strategy}")


def _execute_sequential(
    db: Session,
    plan: Any,
    suites: List[Any],
    platform: str,
    device_serial: Optional[str],
    profile_id: Optional[int],
    timeout: Optional[int],
    extra_args: Optional[Dict[str, Any]],
    priority: Optional[int],
    test_plan_task_id: str
) -> tuple[Optional[List[RunResponse]], Optional[ServiceValidationError]]:
    """Execute test plan suites sequentially"""
    # Only create the test plan record, don't create individual suite records
    # The test plan record will be enqueued as a single task

    # Collect suite IDs for the task queue
    suite_ids = [tps.suite_id for tps in suites]
    suite_names = []
    for tps in suites:
        suite = db.get(Suite, tps.suite_id)
        if suite:
            suite_names.append({'id': suite.id, 'name': suite.name})

    # Create task data for the test plan
    task_data = {
        "type": "test_plan",
        "target_ids": suite_ids,
        "targets": suite_names,
        "platform": platform,
        "device_serial": device_serial,
        "device_name": None,
        "profile_id": profile_id,
        "timeout": timeout,
        "extra_args": extra_args,
        "priority": priority,
    }

    # Enqueue the test plan task
    from app.utils.task_queue import get_task_queue
    from app.services.run_orchestrator import get_run_orchestrator

    task_queue = get_task_queue()
    queued = task_queue.put_nowait(test_plan_task_id, task_data, priority=priority)
    if not queued:
        # Mark test plan as failed
        history_repo = RunHistoryRepository(db)
        run = history_repo.get_by_task_id(test_plan_task_id)
        if run:
            _persist_run_state(run, db, db_result="fail", finished=True)
        return None, ServiceValidationError(code=5000, message="Failed to enqueue test plan task")

    # Create orchestrator task for tracking
    orchestrator = get_run_orchestrator()
    orchestrator.cleanup_expired(ttl_seconds=21600)
    orchestrator.create_task(test_plan_task_id, suite_names)

    # Return the test plan response
    plan_response = RunResponse(
        task_id=test_plan_task_id,
        type='test_plan',
        targets=suite_names,
        status='pending',
        cmd=['testflow', 'run', test_plan_task_id],
        started_at=datetime.utcnow()
    )

    return [plan_response], None


def _persist_run_state(
    run: object,
    db: Session,
    *,
    db_result: Optional[str] = None,
    finished: bool = False,
) -> None:
    if db_result is not None:
        run.result = db_result
    if finished:
        run.finished_at = datetime.utcnow()
    db.commit()


def _execute_parallel(
    db: Session,
    plan: Any,
    suites: List[Any],
    platform: str,
    device_serial: Optional[str],
    profile_id: Optional[int],
    timeout: Optional[int],
    extra_args: Optional[Dict[str, Any]],
    priority: Optional[int],
    test_plan_task_id: str
) -> tuple[Optional[List[RunResponse]], Optional[ServiceValidationError]]:
    """
    Execute test plan suites in parallel
    TODO: Implement parallel execution logic
    For now, use sequential execution
    """
    # For now, use sequential execution
    return _execute_sequential(
        db,
        plan,
        suites,
        platform,
        device_serial,
        profile_id,
        timeout,
        extra_args,
        priority,
        test_plan_task_id
    )


def build_test_plan_response(db: Session, plan: Any) -> Dict[str, Any]:
    """Build test plan response dictionary"""
    from app.models.test_plan import TestPlanSuite
    suite_count = db.execute(
        select(func.count(TestPlanSuite.id)).where(TestPlanSuite.test_plan_id == plan.id)
    ).scalar() or 0

    return {
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
    }
