"""
Configuration management
"""
import os
import json
import logging
from typing import Optional, Union, List
from pydantic import field_validator
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
    cors_origins: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:5000", "ws://localhost:5000", "ws://localhost:8000"]

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

    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """解析 CORS origins，支持逗号分隔的字符串或 JSON 数组"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # 尝试解析 JSON
            if v.startswith('['):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # 解析逗号分隔的字符串
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_security_settings()

    def _validate_security_settings(self):
        """验证安全配置"""
        # 检查生产环境配置 - 更严格的验证
        if not self.debug:
            # 检查auth_secret - 生产环境必须设置
            if not self.auth_secret or self.auth_secret in ["change-me-in-production", ""]:
                raise ValueError(
                    "SECURITY ERROR: AUTH_SECRET must be set in production environment. "
                    "Set a strong random string via AUTH_SECRET environment variable. "
                    "Generate one with: openssl rand -hex 32"
                )

            # 检查加密密钥 - 生产环境必须设置
            if not self.ai_config_encryption_key or self.ai_config_encryption_key in ["change-me-in-production-use-openssl-rand-32", ""]:
                raise ValueError(
                    "SECURITY ERROR: AI_CONFIG_ENCRYPTION_KEY must be set in production environment. "
                    "Set a strong random string via AI_CONFIG_ENCRYPTION_KEY environment variable. "
                    "Generate one with: openssl rand -hex 32"
                )

            # 检查密钥长度 - 至少32字符
            if len(self.auth_secret) < 32:
                raise ValueError(
                    f"SECURITY ERROR: AUTH_SECRET too short ({len(self.auth_secret)} chars). "
                    "Use at least 32 characters. Generate with: openssl rand -hex 32"
                )

            if len(self.ai_config_encryption_key) < 32:
                raise ValueError(
                    f"SECURITY ERROR: AI_CONFIG_ENCRYPTION_KEY too short ({len(self.ai_config_encryption_key)} chars). "
                    "Use at least 32 characters. Generate with: openssl rand -hex 32"
                )

        # 开发环境给出提示但不阻止启动
        if self.debug:
            if not self.auth_secret or self.auth_secret == "change-me-in-production":
                logger.warning(
                    "Development mode: Using default auth_secret. "
                    "For production, generate a secure key: openssl rand -hex 32"
                )
            if not self.ai_config_encryption_key or self.ai_config_encryption_key == "change-me-in-production-use-openssl-rand-32":
                logger.warning(
                    "Development mode: Using default encryption key. "
                    "For production, generate a secure key: openssl rand -hex 32"
                )


# Create settings instance
settings = Settings()
