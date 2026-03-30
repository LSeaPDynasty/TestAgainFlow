"""
FastAPI application entry point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.routers import api_router, websocket_router
from app.schemas.common import ApiResponse
from app.middleware import setup_error_handlers, RequestContextMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Initializing TestFlow API...")
    # Skip database initialization during tests
    import os
    if not os.getenv("PYTEST_CURRENT_TEST"):
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.warning(f"Database initialization failed: {e}")
            logger.warning("API will start but database operations may fail")
    else:
        logger.info("Running in test mode - skipping database initialization")

    # 启动缓存清理任务
    import asyncio
    from app.utils.cache import cache
    from app.services.websocket_service import get_cleanup_task

    async def cache_cleanup_task():
        """定期清理过期缓存"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                count = cache.cleanup_expired()
                if count > 0:
                    logger.info(f"Cleaned up {count} expired cache entries")
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    # 启动后台清理任务
    cleanup_task = asyncio.create_task(cache_cleanup_task())
    ws_cleanup_task = get_cleanup_task()  # 启动WebSocket清理任务

    yield

    # Shutdown
    logger.info("Shutting down TestFlow API...")
    # 取消清理任务
    cleanup_task.cancel()
    ws_cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    try:
        await ws_cleanup_task
    except asyncio.CancelledError:
        pass


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="TestFlow Automation Testing Platform API",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 使用配置中的允许源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request context middleware
app.add_middleware(RequestContextMiddleware)

# Setup unified error handling
setup_error_handlers(app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Include WebSocket routes
app.include_router(websocket_router)


@app.get("/", response_model=ApiResponse)
def root():
    """Root endpoint"""
    from app.utils.response import ok
    return ok(data={
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    })


@app.get("/health", response_model=ApiResponse)
def health_check():
    """Health check endpoint"""
    from app.utils.response import ok
    from app.services.system_health import collect_health_snapshot

    return ok(data=collect_health_snapshot().to_dict())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
