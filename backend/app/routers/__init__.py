"""Routers package initialization."""
from fastapi import APIRouter

from .backups import router as backups_router
from .cache import router as cache_router
from .data_store import router as data_store_router
from .devices import router as devices_router
from .elements import router as elements_router
from .executor_status import router as executor_status_router
from .executor_capabilities import router as executor_capabilities_router
from .flows import router as flows_router
from .health import router as health_router
from .history import router as history_router
from .impact import router as impact_router
from .bulk_import import router as bulk_import_router
from .profiles import router as profiles_router
from .projects import router as projects_router
from .permissions import router as permissions_router
from .reports import router as reports_router
from .run_logs import router as run_logs_router
from .runs import router as runs_router
from .screens import router as screens_router
from .scheduler import router as scheduler_router
from .scheduled_jobs import router as scheduled_jobs_router
from .steps import router as steps_router
from .suites import router as suites_router
from .tags import router as tags_router
from .test_plans import router as test_plans_router
from .task_queue_ws import router as task_queue_ws_router
from .testcases import router as testcases_router
from .users import router as users_router
from .websocket import router as websocket_base_router
from .ai import router as ai_router

api_router = APIRouter()

api_router.include_router(screens_router)
api_router.include_router(scheduler_router)
api_router.include_router(elements_router)
api_router.include_router(steps_router)
api_router.include_router(flows_router)
api_router.include_router(testcases_router)
api_router.include_router(suites_router)
api_router.include_router(test_plans_router)
api_router.include_router(tags_router)
api_router.include_router(profiles_router)
api_router.include_router(data_store_router)
api_router.include_router(devices_router)
api_router.include_router(runs_router)
api_router.include_router(history_router)
api_router.include_router(backups_router)
api_router.include_router(impact_router)
api_router.include_router(reports_router)
api_router.include_router(health_router)
api_router.include_router(executor_status_router)
api_router.include_router(executor_capabilities_router)
api_router.include_router(run_logs_router)
api_router.include_router(projects_router)
api_router.include_router(scheduled_jobs_router)
api_router.include_router(users_router)
api_router.include_router(bulk_import_router)
api_router.include_router(ai_router)
api_router.include_router(permissions_router)
api_router.include_router(cache_router)

websocket_router = APIRouter()
websocket_router.include_router(websocket_base_router)
websocket_router.include_router(task_queue_ws_router)

__all__ = ["api_router", "websocket_router"]
