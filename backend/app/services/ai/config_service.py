"""
AI Configuration Service
Manages AI provider configurations with encryption
"""
import os
import json
import logging
from typing import Optional, List
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.models.ai_config import AIConfig
from app.models.profile import Profile
from app.config import settings
from ..ai.base import AIProviderConfig, ProviderType
from ..ai.providers import OpenAIProvider, ZhipuProvider, CustomHTTPProvider

logger = logging.getLogger(__name__)


class AIConfigService:
    """AI Configuration Management Service"""

    def __init__(self, db: Session):
        self.db = db
        self._cipher = self._init_cipher()

    def _init_cipher(self) -> Fernet:
        """Initialize encryption cipher"""
        # Try to get key from environment or use default for development
        key = os.getenv("AI_CONFIG_ENCRYPTION_KEY")
        if not key:
            # Generate a key for development (not secure for production)
            key = Fernet.generate_key()
            logger.warning("Using generated encryption key. Set AI_CONFIG_ENCRYPTION_KEY env var for production.")

        # Ensure key is bytes
        if isinstance(key, str):
            key = key.encode()

        return Fernet(key)

    def _encrypt_config(self, config_dict: dict) -> str:
        """Encrypt configuration data"""
        json_str = json.dumps(config_dict)
        return self._cipher.encrypt(json_str.encode()).decode()

    def _decrypt_config(self, encrypted_str: str) -> dict:
        """Decrypt configuration data"""
        decrypted = self._cipher.decrypt(encrypted_str.encode())
        return json.loads(decrypted.decode())

    def get_active_config(self, profile_id: Optional[int] = None) -> Optional[AIConfig]:
        """
        Get active AI configuration

        Priority:
        1. Profile-associated config
        2. Highest priority active config
        3. Environment variables (fallback)
        """
        # Check profile config first
        if profile_id:
            profile = self.db.get(Profile, profile_id)
            if profile and profile.ai_config_id:
                config = self.db.get(AIConfig, profile.ai_config_id)
                if config and config.is_active:
                    return config

        # Get highest priority active config
        stmt = (
            select(AIConfig)
            .where(AIConfig.is_active == True)
            .order_by(AIConfig.priority.desc(), AIConfig.id.asc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_config_by_id(self, config_id: int) -> Optional[AIConfig]:
        """Get configuration by ID"""
        return self.db.get(AIConfig, config_id)

    def list_configs(self, active_only: bool = False) -> List[AIConfig]:
        """List all configurations"""
        stmt = select(AIConfig)
        if active_only:
            stmt = stmt.where(AIConfig.is_active == True)
        stmt = stmt.order_by(AIConfig.priority.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create_config(
        self,
        provider: str,
        name: str,
        config_data: dict,
        priority: int = 1,
        is_active: bool = True
    ) -> AIConfig:
        """Create new AI configuration"""
        # Encrypt sensitive data
        encrypted_config = self._encrypt_config(config_data)

        ai_config = AIConfig(
            provider=provider,
            name=name,
            config=encrypted_config,
            priority=priority,
            is_active=is_active
        )

        self.db.add(ai_config)
        self.db.commit()
        self.db.refresh(ai_config)
        return ai_config

    def update_config(self, config_id: int, **kwargs) -> Optional[AIConfig]:
        """Update configuration"""
        config = self.get_config_by_id(config_id)
        if not config:
            return None

        # If updating config data, encrypt it
        if "config_data" in kwargs:
            kwargs["config"] = self._encrypt_config(kwargs.pop("config_data"))

        for field, value in kwargs.items():
            if hasattr(config, field):
                setattr(config, field, value)

        self.db.commit()
        self.db.refresh(config)
        return config

    def delete_config(self, config_id: int) -> bool:
        """Delete configuration"""
        config = self.get_config_by_id(config_id)
        if not config:
            return False

        self.db.delete(config)
        self.db.commit()
        return True

    def get_provider_config(self, ai_config: AIConfig) -> AIProviderConfig:
        """Get AIProviderConfig from AIConfig model"""
        decrypted_config = self._decrypt_config(ai_config.config)

        return AIProviderConfig(
            provider_type=ai_config.provider,
            api_key=decrypted_config.get("api_key", ""),
            base_url=decrypted_config.get("base_url"),
            model=decrypted_config.get("model", "gpt-3.5-turbo"),
            timeout=decrypted_config.get("timeout", 30),
            max_retries=decrypted_config.get("max_retries", 3),
            extra_params=decrypted_config.get("extra_params", {})
        )

    def get_provider(self, config_id: Optional[int] = None, profile_id: Optional[int] = None):
        """
        Get AI provider instance

        Args:
            config_id: Specific config ID to use
            profile_id: Profile ID to get associated config

        Returns:
            Provider instance (OpenAIProvider, ZhipuProvider, or CustomHTTPProvider)
        """
        # Get config
        if config_id:
            ai_config = self.get_config_by_id(config_id)
        else:
            ai_config = self.get_active_config(profile_id)

        if not ai_config:
            # Try to get from environment variables
            return self._get_provider_from_env()

        provider_config = self.get_provider_config(ai_config)
        return self._create_provider(provider_config)

    def _get_provider_from_env(self):
        """Get provider from environment variables"""
        provider_type = settings.ai_default_provider

        if provider_type == "zhipu":
            # 智谱AI使用OpenAI兼容模式
            return OpenAIProvider(AIProviderConfig(
                provider_type="openai",
                api_key=settings.zhipu_api_key,
                base_url=settings.zhipu_base_url,
                model=settings.zhipu_model
            ))
        else:
            return OpenAIProvider(AIProviderConfig(
                provider_type="openai",
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_model
            ))

    def _create_provider(self, config: AIProviderConfig):
        """Create provider instance from config"""
        provider_map = {
            "openai": OpenAIProvider,
            "zhipu": ZhipuProvider,
            "custom": CustomHTTPProvider
        }

        provider_class = provider_map.get(config.provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {config.provider_type}")

        return provider_class(config)

    def mask_api_key(self, api_key: str) -> str:
        """Mask API key for display"""
        if not api_key or len(api_key) < 8:
            return "****"

        return f"{api_key[:4]}...{api_key[-4:]}"

    def to_dict_safe(self, ai_config: AIConfig) -> dict:
        """Convert AIConfig to dict with masked sensitive data"""
        decrypted_config = self._decrypt_config(ai_config.config)

        return {
            "id": ai_config.id,
            "provider": ai_config.provider,
            "name": ai_config.name,
            "is_active": ai_config.is_active,
            "priority": ai_config.priority,
            "config": {
                **decrypted_config,
                "api_key": self.mask_api_key(decrypted_config.get("api_key", ""))
            },
            "created_at": ai_config.created_at.isoformat(),
            "updated_at": ai_config.updated_at.isoformat()
        }


# Import at the end to avoid circular dependency
from sqlalchemy import select
