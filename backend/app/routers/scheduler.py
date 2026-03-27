"""Scheduler management router."""
from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.schemas.scheduler import SchedulerConfigResponse, SchedulerConfigUpdate
from app.services.scheduler_service import get_scheduler_config, update_scheduler_config
from app.utils.response import ok
from app.utils.task_queue import get_task_queue

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/config", response_model=ApiResponse[SchedulerConfigResponse])
def get_config():
    cfg = get_scheduler_config()
    return ok(data=SchedulerConfigResponse(**cfg.__dict__))


@router.put("/config", response_model=ApiResponse[SchedulerConfigResponse])
def update_config(req: SchedulerConfigUpdate):
    cfg = update_scheduler_config(req.model_dump(exclude_none=True))
    return ok(data=SchedulerConfigResponse(**cfg.__dict__), message="Scheduler config updated")


@router.get("/queue", response_model=ApiResponse)
def get_queue_state():
    queue = get_task_queue()
    return ok(
        data={
            "queue_size": queue.get_queue_size(),
            "statuses": queue.get_all_statuses(),
        }
    )
