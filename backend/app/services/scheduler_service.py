"""In-memory scheduler policy service."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from threading import Lock
from typing import Dict


@dataclass
class SchedulerConfig:
    enabled: bool = True
    max_inflight_tasks: int = 8
    default_priority: int = 5
    queue_strategy: str = "priority_fifo"


_config = SchedulerConfig()
_lock = Lock()


def get_scheduler_config() -> SchedulerConfig:
    with _lock:
        return SchedulerConfig(**asdict(_config))


def update_scheduler_config(payload: Dict[str, object]) -> SchedulerConfig:
    with _lock:
        if "enabled" in payload:
            _config.enabled = bool(payload["enabled"])
        if "max_inflight_tasks" in payload:
            value = int(payload["max_inflight_tasks"])
            _config.max_inflight_tasks = max(1, min(100, value))
        if "default_priority" in payload:
            value = int(payload["default_priority"])
            _config.default_priority = max(1, min(10, value))
        if "queue_strategy" in payload and payload["queue_strategy"]:
            _config.queue_strategy = str(payload["queue_strategy"])
        return SchedulerConfig(**asdict(_config))


def can_dispatch(current_inflight: int) -> bool:
    cfg = get_scheduler_config()
    return cfg.enabled and current_inflight < cfg.max_inflight_tasks


def resolve_priority(request_priority: int | None) -> int:
    cfg = get_scheduler_config()
    if request_priority is None:
        return cfg.default_priority
    return max(1, min(10, int(request_priority)))
