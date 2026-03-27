"""Flows router."""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.repositories.flow_repo import FlowRepository
from app.repositories.step_repo import StepRepository
from app.schemas.common import ApiResponse, ErrorCode, PaginatedResponse
from app.schemas.flow import (
    DslValidateRequest,
    DslValidateResponse,
    FlowCreate,
    FlowDetailResponse,
    FlowDuplicateRequest,
    FlowResponse,
    FlowUpdate,
)
from app.services.flow_service import (
    build_create_payload,
    build_flow_detail_response,
    build_flow_response,
    build_update_payload,
    calculate_expanded_count,
    parse_tag_ids,
    validate_dsl_content,
    validate_flow_create,
)
from app.utils.pagination import calculate_offset
from app.utils.response import error, ok

router = APIRouter(prefix="/flows", tags=["flows"])


@router.get("", response_model=ApiResponse[PaginatedResponse[FlowResponse]])
def list_flows(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: str = Query(None),
    flow_type: str = Query(None),
    tag_ids: str = Query(None),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_session),
):
    """Get flow list."""
    repo = FlowRepository(db)
    skip = calculate_offset(page, page_size)
    results, total = repo.list_with_details(
        skip=skip,
        limit=page_size,
        search=search,
        flow_type=flow_type,
        tag_ids=parse_tag_ids(tag_ids),
        project_id=project_id,
    )
    return ok(data=PaginatedResponse(items=results, total=total, page=page, page_size=page_size))


@router.get("/{flow_id}", response_model=ApiResponse[FlowDetailResponse])
def get_flow(flow_id: int, db: Session = Depends(get_db_session)):
    """Get flow by ID with steps."""
    repo = FlowRepository(db)
    flow = repo.get_with_details(flow_id)
    if not flow:
        return error(code=ErrorCode.NOT_FOUND, message="Flow not found")
    return ok(data=build_flow_detail_response(db, flow, repo))


@router.post("", response_model=ApiResponse[FlowResponse])
def create_flow(flow_in: FlowCreate, db: Session = Depends(get_db_session)):
    """Create flow."""
    repo = FlowRepository(db)
    step_repo = StepRepository(db)

    validation = validate_flow_create(flow_in, repo, step_repo)
    if validation:
        return error(code=validation.code, message=validation.message)

    flow = repo.create_with_steps(build_create_payload(flow_in))
    expanded_count = calculate_expanded_count(flow_in.flow_type, flow_in.dsl_content, len(flow.flow_steps))
    return ok(data=build_flow_response(flow, repo, expanded_step_count=expanded_count), message="Flow created successfully")


@router.put("/{flow_id}", response_model=ApiResponse[FlowResponse])
def update_flow(flow_id: int, flow_in: FlowUpdate, db: Session = Depends(get_db_session)):
    """Update flow."""
    repo = FlowRepository(db)
    flow = repo.get(flow_id)
    if not flow:
        return error(code=ErrorCode.NOT_FOUND, message="Flow not found")

    if flow_in.name and flow_in.name != flow.name and repo.get_by_name(flow_in.name):
        return error(code=ErrorCode.CONFLICT, message="Flow name already exists")

    updated = repo.update_with_steps(flow_id, build_update_payload(flow, flow_in))
    return ok(data=build_flow_response(updated, repo), message="Flow updated successfully")


@router.delete("/{flow_id}", response_model=ApiResponse)
def delete_flow(flow_id: int, db: Session = Depends(get_db_session)):
    """Delete flow."""
    repo = FlowRepository(db)
    testcase_count = repo.check_testcase_usage(flow_id)
    if testcase_count > 0:
        return error(
            code=ErrorCode.DEPENDENCY_ERROR,
            message="Flow is referenced by testcases",
            data={"referenced_by_testcases_count": testcase_count},
        )

    if not repo.delete(flow_id):
        return error(code=ErrorCode.NOT_FOUND, message="Flow not found")
    return ok(message="Flow deleted successfully")


@router.post("/{flow_id}/duplicate", response_model=ApiResponse[FlowResponse])
def duplicate_flow(flow_id: int, req: FlowDuplicateRequest, db: Session = Depends(get_db_session)):
    """Duplicate flow."""
    repo = FlowRepository(db)

    if repo.get_by_name(req.new_name):
        return error(code=ErrorCode.CONFLICT, message="Flow name already exists")

    new_flow = repo.duplicate(flow_id, req.new_name)
    if not new_flow:
        return error(code=ErrorCode.NOT_FOUND, message="Flow not found")

    return ok(data=build_flow_response(new_flow, repo), message="Flow duplicated successfully")


@router.post("/validate-dsl", response_model=ApiResponse[DslValidateResponse])
def validate_dsl(req: DslValidateRequest, db: Session = Depends(get_db_session)):
    """Validate DSL content."""
    return ok(data=validate_dsl_content(db, req.dsl_content))
