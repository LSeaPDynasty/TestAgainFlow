"""System health snapshot service."""
from __future__ import annotations

from dataclasses import dataclass
import time

from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.services.run_orchestrator import get_run_orchestrator

_PROCESS_START_TIME = time.time()


@dataclass
class HealthSnapshot:
    status: str
    version: str
    db_connected: bool
    adb_available: bool
    running_tasks: int
    uptime_seconds: int

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "version": self.version,
            "db_connected": self.db_connected,
            "adb_available": self.adb_available,
            "running_tasks": self.running_tasks,
            "uptime_seconds": self.uptime_seconds,
        }


def _check_db_connected() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def _check_adb_available() -> bool:
    try:
        from app.utils.adb import get_adb_devices

        get_adb_devices()
        return True
    except Exception:
        return False


def collect_health_snapshot() -> HealthSnapshot:
    orchestrator = get_run_orchestrator()
    running_tasks = sum(
        1 for status in orchestrator.list_statuses().values() if status == "running"
    )
    db_connected = _check_db_connected()

    return HealthSnapshot(
        status="ok" if db_connected else "degraded",
        version=settings.app_version,
        db_connected=db_connected,
        adb_available=_check_adb_available(),
        running_tasks=running_tasks,
        uptime_seconds=int(time.time() - _PROCESS_START_TIME),
    )
