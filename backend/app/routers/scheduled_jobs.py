"""Scheduled Jobs router - automated test execution management"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.repositories.scheduled_job_repo import ScheduledJobRepository
from app.repositories.testcase_repo import TestcaseRepository
from app.repositories.suite_repo import SuiteRepository
from app.schemas.scheduled_job import *
from app.schemas.common import ApiResponse, PaginatedResponse, ErrorCode
from app.utils.response import ok, error
from app.utils.pagination import calculate_offset
from app.utils.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/scheduled-jobs", tags=["scheduled-jobs"])


@router.get("", response_model=ApiResponse[PaginatedResponse])
def list_scheduled_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    enabled_only: bool = Query(False),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db_session)
):
    """List scheduled jobs"""
    repo = ScheduledJobRepository(db)
    skip = calculate_offset(page, page_size)

    results, total = repo.list_with_details(
        skip=skip,
        limit=page_size,
        enabled_only=enabled_only,
        project_id=project_id
    )

    response_data = PaginatedResponse(
        items=results,
        total=total,
        page=page,
        page_size=page_size
    )
    return ok(data=response_data)


@router.get("/{job_id}", response_model=ApiResponse[ScheduledJobResponse])
def get_scheduled_job(
    job_id: int,
    db: Session = Depends(get_db_session)
):
    """Get scheduled job by ID"""
    repo = ScheduledJobRepository(db)
    job = repo.get_with_details(job_id)

    if not job:
        return error(code=ErrorCode.NOT_FOUND, message=f"Scheduled job not found: id={job_id}")

    response_data = ScheduledJobResponse(
        id=job.id,
        name=job.name,
        description=job.description,
        job_type=job.job_type,
        target_id=job.target_id,
        cron_expression=job.cron_expression,
        device_serial=job.device_serial,
        enabled=job.enabled,
        status=job.status.value,
        last_run_time=job.last_run_time,
        next_run_time=job.next_run_time,
        last_run_status=job.last_run_status,
        last_run_message=job.last_run_message,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at
    )
    return ok(data=response_data)


@router.post("", response_model=ApiResponse[ScheduledJobResponse])
def create_scheduled_job(
    job_in: ScheduledJobCreate,
    db: Session = Depends(get_db_session)
):
    """Create scheduled job"""
    repo = ScheduledJobRepository(db)
    tc_repo = TestcaseRepository(db)
    suite_repo = SuiteRepository(db)

    # Validate name
    if not job_in.name or not job_in.name.strip():
        return error(code=ErrorCode.VALIDATION_ERROR, message="Job name cannot be empty")

    # Check duplicate name
    if repo.get_by_name(job_in.name):
        return error(code=ErrorCode.CONFLICT, message="Job name already exists")

    # Validate cron expression
    try:
        from croniter import croniter
        croniter(job_in.cron_expression)
    except Exception as e:
        return error(code=ErrorCode.VALIDATION_ERROR, message=f"Invalid cron expression: {str(e)}")

    # Validate target exists
    if job_in.job_type == "testcase":
        testcase = tc_repo.get(job_in.target_id)
        if not testcase:
            return error(code=ErrorCode.NOT_FOUND, message=f"Testcase not found: id={job_in.target_id}")
    else:  # suite
        suite = suite_repo.get(job_in.target_id)
        if not suite:
            return error(code=ErrorCode.NOT_FOUND, message=f"Suite not found: id={job_in.target_id}")

    # Create job
    job_data = job_in.model_dump()
    job = repo.create(job_data)
    db.refresh(job)

    response_data = ScheduledJobResponse(
        id=job.id,
        name=job.name,
        description=job.description,
        job_type=job.job_type,
        target_id=job.target_id,
        cron_expression=job.cron_expression,
        device_serial=job.device_serial,
        enabled=job.enabled,
        status=job.status.value,
        last_run_time=job.last_run_time,
        next_run_time=job.next_run_time,
        last_run_status=job.last_run_status,
        last_run_message=job.last_run_message,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at
    )
    return ok(data=response_data, message="Scheduled job created successfully")


@router.put("/{job_id}", response_model=ApiResponse[ScheduledJobResponse])
def update_scheduled_job(
    job_id: int,
    job_in: ScheduledJobUpdate,
    db: Session = Depends(get_db_session)
):
    """Update scheduled job"""
    repo = ScheduledJobRepository(db)
    job = repo.get(job_id)

    if not job:
        return error(code=ErrorCode.NOT_FOUND, message=f"Scheduled job not found: id={job_id}")

    # Check duplicate name
    if job_in.name and job_in.name != job.name:
        if repo.get_by_name(job_in.name):
            return error(code=ErrorCode.CONFLICT, message="Job name already exists")

    # Validate cron expression if provided
    if job_in.cron_expression:
        try:
            from croniter import croniter
            croniter(job_in.cron_expression)
        except Exception as e:
            return error(code=ErrorCode.VALIDATION_ERROR, message=f"Invalid cron expression: {str(e)}")

    # Update fields
    update_data = job_in.model_dump(exclude_none=True)
    for field, value in update_data.items():
        if hasattr(job, field):
            setattr(job, field, value)

    db.commit()
    db.refresh(job)

    response_data = ScheduledJobResponse(
        id=job.id,
        name=job.name,
        description=job.description,
        job_type=job.job_type,
        target_id=job.target_id,
        cron_expression=job.cron_expression,
        device_serial=job.device_serial,
        enabled=job.enabled,
        status=job.status.value,
        last_run_time=job.last_run_time,
        next_run_time=job.next_run_time,
        last_run_status=job.last_run_status,
        last_run_message=job.last_run_message,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at
    )
    return ok(data=response_data, message="Scheduled job updated successfully")


@router.delete("/{job_id}", response_model=ApiResponse)
def delete_scheduled_job(
    job_id: int,
    db: Session = Depends(get_db_session)
):
    """Delete scheduled job"""
    repo = ScheduledJobRepository(db)

    if not repo.delete(job_id):
        return error(code=ErrorCode.NOT_FOUND, message=f"Scheduled job not found: id={job_id}")

    return ok(message="Scheduled job deleted successfully")


@router.post("/{job_id}/run", response_model=ApiResponse)
def run_scheduled_job(
    job_id: int,
    req: JobRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """Manually run a scheduled job"""
    repo = ScheduledJobRepository(db)
    job = repo.get(job_id)

    if not job:
        return error(code=ErrorCode.NOT_FOUND, message=f"Scheduled job not found: id={job_id}")

    # Create run task
    from app.utils.task_queue import get_task_queue
    queue = get_task_queue()

    task_data = {
        "type": job.job_type,
        "target_ids": [job.target_id],
        "device_serial": req.device_serial,
        "priority": 5,
        "scheduled_job_id": job.id
    }

    task_id = queue.add_task(**task_data)

    return ok(data={
        "task_id": task_id,
        "message": f"Job '{job.name}' started successfully"
    }, message="Job execution started")


@router.post("/{job_id}/toggle", response_model=ApiResponse[ScheduledJobResponse])
def toggle_scheduled_job(
    job_id: int,
    db: Session = Depends(get_db_session)
):
    """Toggle scheduled job enabled status"""
    repo = ScheduledJobRepository(db)
    job = repo.get(job_id)

    if not job:
        return error(code=ErrorCode.NOT_FOUND, message=f"Scheduled job not found: id={job_id}")

    job.enabled = not job.enabled
    db.commit()
    db.refresh(job)

    response_data = ScheduledJobResponse(
        id=job.id,
        name=job.name,
        description=job.description,
        job_type=job.job_type,
        target_id=job.target_id,
        cron_expression=job.cron_expression,
        device_serial=job.device_serial,
        enabled=job.enabled,
        status=job.status.value,
        last_run_time=job.last_run_time,
        next_run_time=job.next_run_time,
        last_run_status=job.last_run_status,
        last_run_message=job.last_run_message,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at
    )
    return ok(data=response_data, message=f"Job {'enabled' if job.enabled else 'disabled'} successfully")
