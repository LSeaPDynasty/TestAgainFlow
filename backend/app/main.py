"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.routers import api_router, websocket_router
from app.schemas.common import ApiResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Initializing TestFlow API...")
    # Skip database initialization during tests
    import os
    if not os.getenv("PYTEST_CURRENT_TEST"):
        try:
            init_db()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Warning: Database initialization failed: {e}")
            print("API will start but database operations may fail")
    else:
        print("Running in test mode - skipping database initialization")
    yield
    # Shutdown
    print("Shutting down TestFlow API...")


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
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
