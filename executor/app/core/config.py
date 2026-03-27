"""
Execution Engine Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Execution Engine Settings"""

    # Service
    service_name: str = "TestFlow Execution Engine"
    log_level: str = "INFO"

    # ADB Configuration
    adb_path: str = "adb"
    adb_timeout: int = 30  # seconds
    default_device_timeout: int = 120  # seconds for device operations

    # Execution Configuration
    max_concurrent_executions: int = 5
    execution_timeout: int = 3600  # 1 hour max per execution
    step_timeout: int = 60  # 60 seconds max per step
    screenshot_on_failure: bool = True
    screenshot_dir: str = "./screenshots"

    # Backend API Configuration (for status updates)
    backend_api_url: str = "http://localhost:8000/api/v1"

    # Retry Configuration
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds

    # WebSocket Configuration
    ws_enabled: bool = True
    ws_port: int = 8002

    # Capability Registration Configuration
    backend_url: str = "http://localhost:8000"
    executor_version: str = "1.0.0"
    executor_id_suffix: str = "001"
    heartbeat_interval: int = 30  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
