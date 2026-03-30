"""
Configuration management
"""
import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "TestFlow API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./testflow.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # RabbitMQ (optional)
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # Execution Engine
    engine_transport: str = "ws"  # ws or rabbitmq
    engine_ws_url: str = "ws://localhost:8001/ws"

    # CORS
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000", "http://localhost:5000", "ws://localhost:5000", "ws://localhost:8000"]

    # File storage
    screenshots_dir: str = "./data/screenshots"
    backups_dir: str = "./data/backups"
    custom_flows_dir: str = "./engine/custom_flows"

    # ADB
    adb_path: str = "adb"

    # Auth
    auth_secret: str = "change-me-in-production"
    auth_token_ttl_seconds: int = 86400

    # AI Configuration
    ai_config_encryption_key: str = "change-me-in-production-use-openssl-rand-32"
    ai_default_provider: str = "zhipu"  # 使用智谱AI
    ai_daily_cost_limit: float = 10.0
    ai_cache_ttl: int = 3600

    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-3.5-turbo"

    # Zhipu AI (从.env文件读取)
    zhipu_api_key: str = ""
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    zhipu_model: str = "glm-5"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_security_settings()

    def _validate_security_settings(self):
        """验证安全配置"""
        # 检查生产环境配置
        if not self.debug:
            # 检查auth_secret
            if self.auth_secret in ["change-me-in-production", ""]:
                logger.warning("SECURITY WARNING: Using default auth_secret in non-debug mode. Set AUTH_SECRET environment variable.")

            # 检查加密密钥
            if self.ai_config_encryption_key in ["change-me-in-production-use-openssl-rand-32", ""]:
                logger.warning("SECURITY WARNING: Using default encryption key in non-debug mode. Set AI_CONFIG_ENCRYPTION_KEY environment variable.")

        # 开发环境也给出提示
        if self.debug:
            if self.auth_secret == "change-me-in-production":
                logger.info("Development mode: Using default auth_secret. For production, set AUTH_SECRET environment variable.")
            if self.ai_config_encryption_key == "change-me-in-production-use-openssl-rand-32":
                logger.info("Development mode: Using default encryption key. For production, set AI_CONFIG_ENCRYPTION_KEY environment variable.")


# Create settings instance
settings = Settings()
