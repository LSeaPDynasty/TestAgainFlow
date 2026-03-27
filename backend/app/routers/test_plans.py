"""TestPlans router."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.schemas.test_plan import (
    TestPlanCreate,
    TestPlanDetailResponse,
    TestPlanResponse,
    TestPlanUpdate,
    TestPlanToggleRequest,
    TestPlanAddSuitesRequest,
    TestPlanRemoveSuitesRequest,
    TestPlanReorderSuitesRequest,
    TestPlanSetTestcaseOrderRequest,
    TestPlanExecuteRequest,
    TestPlanExecuteResponse,
)
from app.schemas.run import RunResponse
from app.services.test_plan_service import (
    create_test_plan,
    delete_test_plan,
    get_test_plan_detail,
    list_test_plans,
    toggle_test_plan,
    update_test_plan,
    add_suites_to_plan,
    remove_suites_from_plan,
    reorder_plan_suites,
    set_suite_testcase_order,
    execute_test_plan,
    ServiceValidationError,
)
from app.utils.pagination import calculate_offset
from app.utils.response import error, ok
from typing import List, Dict, Any

router = APIRouter(prefix="/test-plans", tags=["test-plans"])


@router.get("", response_model=ApiResponse[PaginatedResponse[Dict[str, Any]]])
def list_test_plan_api(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_session),
):
    """Get test plan list."""
    results, total = list_test_plans(
        db,
        skip=calculate_offset(page, page_size),
        limit=page_size,
        project_id=project_id,
    )
    return ok(data=PaginatedResponse(items=results, total=total, page=page, page_size=page_size))


@router.get("/{plan_id}", response_model=ApiResponse[Dict[str, Any]])
def get_test_plan(plan_id: int, db: Session = Depends(get_db_session)):
    """Get test plan by ID."""
    response = get_test_plan_detail(db, plan_id)
    if not response:
        return error(code=ErrorCode.NOT_FOUND, message=f"Test plan not found: id={plan_id}")
    return ok(data=response)


@router.post("", response_model=ApiResponse[Dict[str, Any]])
def create_test_plan_api(plan_in: TestPlanCreate, db: Session = Depends(get_db_session)):
    """Create test plan."""
    response, validation_error = create_test_plan(
        db,
        name=plan_in.name,
        description=plan_in.description,
        execution_strategy=plan_in.execution_strategy,
        max_parallel_tasks=plan_in.max_parallel_tasks,
        project_id=plan_in.project_id,
        suites=[s.model_dump() for s in plan_in.suites] if plan_in.suites else None,
    )
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Test plan created successfully")


@router.put("/{plan_id}", response_model=ApiResponse[Dict[str, Any]])
def update_test_plan_api(plan_id: int, plan_in: TestPlanUpdate, db: Session = Depends(get_db_session)):
    """Update test plan."""
    response, validation_error = update_test_plan(
        db,
        plan_id=plan_id,
        name=plan_in.name,
        description=plan_in.description,
        execution_strategy=plan_in.execution_strategy,
        max_parallel_tasks=plan_in.max_parallel_tasks,
        suites=[s.model_dump() for s in plan_in.suites] if plan_in.suites else None,
    )
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Test plan updated successfully")


@router.delete("/{plan_id}", response_model=ApiResponse)
def delete_test_plan_api(plan_id: int, db: Session = Depends(get_db_session)):
    """Delete test plan."""
    validation_error = delete_test_plan(db, plan_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(message="Test plan deleted successfully")


@router.patch("/{plan_id}/toggle", response_model=ApiResponse[Dict[str, Any]])
def toggle_test_plan_api(plan_id: int, req: TestPlanToggleRequest, db: Session = Depends(get_db_session)):
    """Toggle test plan enabled state."""
    response, validation_error = toggle_test_plan(db, plan_id=plan_id, enabled=req.enabled)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Test plan state updated")


@router.post("/{plan_id}/suites", response_model=ApiResponse[Dict[str, Any]])
def add_suites(plan_id: int, req: TestPlanAddSuitesRequest, db: Session = Depends(get_db_session)):
    """Add suites to test plan."""
    response, validation_error = add_suites_to_plan(db, plan_id=plan_id, suite_ids=req.suite_ids)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Suites added successfully")


@router.delete("/{plan_id}/suites", response_model=ApiResponse[Dict[str, Any]])
def remove_suites(plan_id: int, req: TestPlanRemoveSuitesRequest, db: Session = Depends(get_db_session)):
    """Remove suites from test plan."""
    response, validation_error = remove_suites_from_plan(db, plan_id=plan_id, suite_ids=req.suite_ids)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Suites removed successfully")


@router.put("/{plan_id}/suites/reorder", response_model=ApiResponse[Dict[str, Any]])
def reorder_suites(plan_id: int, req: TestPlanReorderSuitesRequest, db: Session = Depends(get_db_session)):
    """Reorder suites in test plan."""
    suite_orders = [s.model_dump() for s in req.suites]
    response, validation_error = reorder_plan_suites(db, plan_id=plan_id, suite_orders=suite_orders)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Suites reordered successfully")


@router.put("/{plan_id}/suites/{suite_id}/testcases/order", response_model=ApiResponse[Dict[str, Any]])
def set_testcase_order(
    plan_id: int,
    suite_id: int,
    req: TestPlanSetTestcaseOrderRequest,
    db: Session = Depends(get_db_session),
):
    """Set testcase order for a suite in test plan."""
    testcase_orders = [t.model_dump() for t in req.testcase_orders]
    response, validation_error = set_suite_testcase_order(
        db,
        plan_id=plan_id,
        suite_id=suite_id,
        testcase_orders=testcase_orders,
    )
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Testcase order updated successfully")


@router.post("/{plan_id}/run", response_model=ApiResponse[List[Dict[str, Any]]])
def execute_test_plan_api(plan_id: int, req: TestPlanExecuteRequest, db: Session = Depends(get_db_session)):
    """Execute test plan."""
    response, validation_error = execute_test_plan(
        db,
        plan_id=plan_id,
        platform=req.platform,
        device_serial=req.device_serial,
        profile_id=req.profile_id,
        timeout=req.timeout,
        extra_args=req.extra_args,
        priority=req.priority,
    )
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)

    # Convert RunResponse objects to dicts
    response_data = [
        {
            "task_id": r.task_id,
            "type": r.type,
            "targets": r.targets,
            "status": r.status,
            "cmd": r.cmd,
            "started_at": r.started_at,
        }
        for r in response
    ] if response else []

    return ok(data=response_data, message="Test plan execution started")
