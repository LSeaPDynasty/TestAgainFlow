"""Service helpers for run execution endpoints."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.repositories.device_repo import DeviceRepository
from app.repositories.profile_repo import ProfileRepository
from app.repositories.run_history_repo import RunHistoryRepository
from app.repositories.testcase_repo import TestcaseRepository
from app.schemas.run import BatchRunCreate, BatchRunResponse, RunCreate, RunResponse, RunStatusResponse, ScreenshotsResponse
from app.services.run_orchestrator import (
    RUN_STATUS_CANCELLED,
    RUN_STATUS_PAUSED,
    RUN_STATUS_QUEUED,
    RUN_STATUS_RUNNING,
    RUN_STATUS_STOPPED,
    get_run_orchestrator,
)
from app.services.platform_capability_service import (
    collect_actions_for_suites,
    collect_actions_for_testcases,
    get_platform_supported_actions,
    normalize_platform,
)
from app.services.scheduler_service import resolve_priority
from app.services.run_results import build_run_results
from app.services.run_state import map_db_result_to_runtime_status, transition_run_state
from app.utils.task_queue import get_task_queue


@dataclass
class ServiceValidationError:
    code: int
    message: str
    data: Optional[dict] = None


def list_runs(
    db: Session,
    *,
    skip: int,
    limit: int,
    status: Optional[str],
    device_serial: Optional[str],
):
    history_repo = RunHistoryRepository(db)
    return history_repo.list_with_details(
        skip=skip,
        limit=limit,
        status=status,
        device_serial=device_serial,
    )


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


def _resolve_targets(db: Session, run_in: RunCreate) -> tuple[Optional[List[Dict[str, object]]], Optional[Dict[int, int]], Optional[ServiceValidationError]]:
    targets: List[Dict[str, object]] = []
    suite_testcases_count: Dict[int, int] = {}

    if run_in.type == "testcase":
        tc_repo = TestcaseRepository(db)
        for target_id in run_in.target_ids:
            testcase = tc_repo.get(target_id)
            if not testcase:
                return None, None, ServiceValidationError(code=4004, message=f"Testcase not found: id={target_id}")
            targets.append({"id": testcase.id, "name": testcase.name})
        return targets, suite_testcases_count, None

    from app.repositories.suite_repo import SuiteRepository

    suite_repo = SuiteRepository(db)
    for target_id in run_in.target_ids:
        suite = suite_repo.get_with_testcases(target_id)
        if not suite:
            return None, None, ServiceValidationError(code=4004, message=f"Suite not found: id={target_id}")
        targets.append({"id": suite.id, "name": suite.name})
        suite_testcases_count[target_id] = len(suite.suite_testcases)
    return targets, suite_testcases_count, None


def start_run(db: Session, run_in: RunCreate) -> tuple[Optional[RunResponse], Optional[ServiceValidationError]]:
    run_in.platform = normalize_platform(run_in.platform)
    if run_in.type not in {"testcase", "suite"}:
        return None, ServiceValidationError(
            code=4001,
            message=f"Invalid type: {run_in.type}. Must be 'testcase' or 'suite'",
        )
    if not run_in.target_ids:
        return None, ServiceValidationError(code=4001, message="target_ids cannot be empty")

    supported_actions = get_platform_supported_actions(run_in.platform)
    if supported_actions is None:
        return None, ServiceValidationError(
            code=4001,
            message=f"Unsupported platform: {run_in.platform}. Must be one of android/ios/web",
        )

    if run_in.type == "testcase":
        required_actions = collect_actions_for_testcases(db, run_in.target_ids)
    else:
        required_actions = collect_actions_for_suites(db, run_in.target_ids)

    unsupported_actions = sorted(required_actions - supported_actions)
    if unsupported_actions:
        return None, ServiceValidationError(
            code=4001,
            message=(
                f"Platform '{run_in.platform}' does not support actions: "
                + ", ".join(unsupported_actions)
            ),
            data={
                "platform": run_in.platform,
                "unsupported_actions": unsupported_actions,
            },
        )

    targets, suite_testcases_count, target_error = _resolve_targets(db, run_in)
    if target_error:
        return None, target_error

    profile_name = None
    if run_in.profile_id:
        profile_repo = ProfileRepository(db)
        profile = profile_repo.get(run_in.profile_id)
        if not profile:
            return None, ServiceValidationError(code=4004, message=f"Profile not found: id={run_in.profile_id}")
        profile_name = profile.name

    device_name = None
    if run_in.device_serial:
        device_repo = DeviceRepository(db)
        device = device_repo.get_by_serial(run_in.device_serial)
        if not device:
            return None, ServiceValidationError(code=4004, message=f"Device not found: serial={run_in.device_serial}")
        device_name = device.name

        from app.utils.adb import check_device_online

        try:
            if not check_device_online(run_in.device_serial):
                return None, ServiceValidationError(code=4001, message=f"Device is offline: {run_in.device_serial}")
        except Exception as exc:
            return None, ServiceValidationError(code=4001, message=f"Failed to check device status: {exc}")

    task_id = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    history_repo = RunHistoryRepository(db)
    assert targets is not None
    for target in targets:
        history_data = {
            "task_id": task_id,
            "type": run_in.type,
            "target_id": target["id"],
            "target_name": target["name"],
            "result": "pending",
            "profile_id": run_in.profile_id,
            "profile_name": profile_name,
            "device_serial": run_in.device_serial,
            "device_name": device_name,
            "started_at": datetime.utcnow(),
            "total_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
        }
        if run_in.type == "suite":
            history_data["total_count"] = suite_testcases_count.get(target["id"], 0) if suite_testcases_count else 0
        history_repo.create(history_data)

    task_data = {
        "type": run_in.type,
        "target_ids": run_in.target_ids,
        "targets": targets,
        "platform": run_in.platform,
        "device_serial": run_in.device_serial,
        "device_name": device_name,
        "profile_id": run_in.profile_id,
        "timeout": run_in.timeout,
        "extra_args": run_in.extra_args,
        "priority": resolve_priority(run_in.priority),
    }
    task_queue = get_task_queue()
    queued = task_queue.put_nowait(task_id, task_data, priority=task_data["priority"])
    if not queued:
        run = history_repo.get_by_task_id(task_id)
        if run:
            _persist_run_state(run, db, db_result="fail", finished=True)
        return None, ServiceValidationError(code=5000, message="Failed to enqueue task")

    orchestrator = get_run_orchestrator()
    orchestrator.cleanup_expired(ttl_seconds=21600)
    orchestrator.create_task(task_id, targets)

    return (
        RunResponse(
            task_id=task_id,
            type=run_in.type,
            targets=targets,
            status="pending",
            cmd=["testflow", "run", task_id],
            started_at=datetime.utcnow(),
        ),
        None,
    )


def get_run_status(db: Session, task_id: str) -> tuple[Optional[RunStatusResponse], Optional[ServiceValidationError]]:
    history_repo = RunHistoryRepository(db)
    run = history_repo.get_by_task_id(task_id)
    if not run:
        return None, ServiceValidationError(code=4004, message="Task not found")
    orchestrator = get_run_orchestrator()
    status = orchestrator.get_status(task_id) or map_db_result_to_runtime_status(run.result)
    return (
        RunStatusResponse(
            task_id=task_id,
            status=status,
            started_at=run.started_at,
            finished_at=run.finished_at,
            returncode=run.returncode,
            result=run.result,
        ),
        None,
    )


def _transition_run(
    db: Session,
    *,
    task_id: str,
    allowed_current: set[str],
    target_status: str,
    persist_result: Optional[str] = None,
    finish: bool = False,
) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    history_repo = RunHistoryRepository(db)
    run = history_repo.get_by_task_id(task_id)
    if not run:
        return None, ServiceValidationError(code=4004, message="Task not found")

    transition = transition_run_state(
        task_id=task_id,
        db_result=run.result,
        allowed_current=allowed_current,
        target_status=target_status,
    )
    if not transition.ok:
        return None, ServiceValidationError(code=4001, message=transition.error_message or "Invalid transition")

    if persist_result is not None or finish:
        _persist_run_state(run, db, db_result=persist_result, finished=finish)

    return {"task_id": task_id, "status": target_status}, None


def stop_run(db: Session, task_id: str) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    return _transition_run(
        db,
        task_id=task_id,
        allowed_current={RUN_STATUS_QUEUED, RUN_STATUS_RUNNING, RUN_STATUS_PAUSED},
        target_status=RUN_STATUS_STOPPED,
        persist_result="cancelled",
        finish=True,
    )


def pause_run(db: Session, task_id: str) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    return _transition_run(
        db,
        task_id=task_id,
        allowed_current={RUN_STATUS_RUNNING, RUN_STATUS_QUEUED},
        target_status=RUN_STATUS_PAUSED,
    )


def resume_run(db: Session, task_id: str) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    return _transition_run(
        db,
        task_id=task_id,
        allowed_current={RUN_STATUS_PAUSED, RUN_STATUS_QUEUED, RUN_STATUS_RUNNING},
        target_status=RUN_STATUS_RUNNING,
        persist_result="running",
    )


def cancel_run(db: Session, task_id: str) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    return _transition_run(
        db,
        task_id=task_id,
        allowed_current={RUN_STATUS_QUEUED, RUN_STATUS_RUNNING, RUN_STATUS_PAUSED},
        target_status=RUN_STATUS_CANCELLED,
        persist_result="cancelled",
        finish=True,
    )


def get_screenshots(db: Session, task_id: str) -> tuple[Optional[ScreenshotsResponse], Optional[ServiceValidationError]]:
    history_repo = RunHistoryRepository(db)
    run = history_repo.get_by_task_id(task_id)
    if not run:
        return None, ServiceValidationError(code=4004, message="Task not found")
    return ScreenshotsResponse(screenshots=[]), None


def get_run_results(db: Session, task_id: str) -> tuple[Optional[dict], Optional[ServiceValidationError]]:
    history_repo = RunHistoryRepository(db)
    run = history_repo.get_by_task_id(task_id)
    if not run:
        return None, ServiceValidationError(code=4004, message="Task not found")
    return build_run_results(db, run), None


def start_batch_run(db: Session, batch_in: BatchRunCreate) -> tuple[Optional[BatchRunResponse], Optional[ServiceValidationError]]:
    if batch_in.type not in {"testcase", "suite"}:
        return None, ServiceValidationError(code=4001, message="Invalid type")
    if not batch_in.target_ids:
        return None, ServiceValidationError(code=4001, message="target_ids cannot be empty")

    task_ids: List[str] = []
    for target_id in batch_in.target_ids:
        run_req = RunCreate(
            type=batch_in.type,
            target_ids=[target_id],
            profile_id=batch_in.profile_id,
            platform=batch_in.platform,
            device_serial=batch_in.device_serial,
            timeout=batch_in.timeout,
            extra_args=batch_in.extra_args,
            priority=batch_in.priority,
        )
        response, err = start_run(db, run_req)
        if err:
            return None, err
        assert response is not None
        task_ids.append(response.task_id)
    return BatchRunResponse(task_ids=task_ids, mode=batch_in.mode), None
