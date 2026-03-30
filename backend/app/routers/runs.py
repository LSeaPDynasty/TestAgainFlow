"""Runs router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, require_auth
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.run import BatchRunCreate, BatchRunResponse, LogEvent, RunCreate, RunResponse, RunStatusResponse, ScreenshotsResponse
from app.services.run_orchestrator import (
    RUN_STATUS_CANCELLED,
    RUN_STATUS_FAILED,
    RUN_STATUS_STOPPED,
    RUN_STATUS_SUCCESS,
    get_run_orchestrator,
)
from app.services.run_service import (
    cancel_run as cancel_run_service,
    get_run_results as get_run_results_service,
    get_run_status as get_run_status_service,
    get_screenshots as get_screenshots_service,
    list_runs as list_runs_service,
    pause_run as pause_run_service,
    resume_run as resume_run_service,
    start_batch_run as start_batch_run_service,
    start_run as start_run_service,
    stop_run as stop_run_service,
)
from app.utils.pagination import calculate_offset
from app.utils.response import error, ok

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=ApiResponse[PaginatedResponse])
def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    device_serial: str | None = Query(None),
    db: Session = Depends(get_db_session),
):
    results, total = list_runs_service(
        db,
        skip=calculate_offset(page, page_size),
        limit=page_size,
        status=status,
        device_serial=device_serial,
    )
    return ok(data=PaginatedResponse(items=results, total=total, page=page, page_size=page_size))


@router.post("", response_model=ApiResponse[RunResponse])
def start_run(
    run_in: RunCreate,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    response, validation_error = start_run_service(db, run_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Task queued")


@router.get("/{task_id}", response_model=ApiResponse[RunStatusResponse])
def get_run_status(task_id: str, db: Session = Depends(get_db_session)):
    response, validation_error = get_run_status_service(db, task_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)


@router.get("/{task_id}/status", response_model=ApiResponse[RunStatusResponse])
def get_run_status_alias(task_id: str, db: Session = Depends(get_db_session)):
    return get_run_status(task_id, db)


@router.post("/{task_id}/stop", response_model=ApiResponse)
def stop_run(
    task_id: str,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    response, validation_error = stop_run_service(db, task_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Task stopped")


@router.post("/{task_id}/pause", response_model=ApiResponse)
def pause_run(
    task_id: str,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    response, validation_error = pause_run_service(db, task_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Task paused")


@router.post("/{task_id}/resume", response_model=ApiResponse)
def resume_run(
    task_id: str,
    db: Session = Depends(get_db_session),
    auth: dict = Depends(require_auth)
):
    response, validation_error = resume_run_service(db, task_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Task resumed")


@router.get("/{task_id}/logs")
async def get_run_logs(task_id: str):
    orchestrator = get_run_orchestrator()

    async def event_generator():
        task = orchestrator.get_task(task_id)
        if not task:
            yield f"data: {LogEvent(type='error', text='Task not found').model_dump_json()}\n\n"
            return

        for log in task.logs:
            yield f"data: {LogEvent(**log).model_dump_json()}\n\n"

        if task.status in {RUN_STATUS_SUCCESS, RUN_STATUS_FAILED, RUN_STATUS_CANCELLED, RUN_STATUS_STOPPED}:
            done = LogEvent(
                type="done",
                result=task.result.get("result", task.status),
                returncode=task.result.get("returncode"),
                duration=task.result.get("duration"),
            )
            yield f"data: {done.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.delete("/{task_id}", response_model=ApiResponse)
def cancel_run(task_id: str, db: Session = Depends(get_db_session)):
    response, validation_error = cancel_run_service(db, task_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Task cancelled")


@router.get("/{task_id}/screenshots", response_model=ApiResponse[ScreenshotsResponse])
def get_screenshots(task_id: str, db: Session = Depends(get_db_session)):
    response, validation_error = get_screenshots_service(db, task_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)


@router.get("/{task_id}/results", response_model=ApiResponse)
def get_run_results(task_id: str, db: Session = Depends(get_db_session)):
    response, validation_error = get_run_results_service(db, task_id)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response)


@router.post("/batch", response_model=ApiResponse[BatchRunResponse])
def start_batch_run(batch_in: BatchRunCreate, db: Session = Depends(get_db_session)):
    response, validation_error = start_batch_run_service(db, batch_in)
    if validation_error:
        return error(code=validation_error.code, message=validation_error.message, data=validation_error.data)
    return ok(data=response, message="Batch tasks queued")
