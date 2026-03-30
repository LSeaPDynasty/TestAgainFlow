"""
AI服务包装器 - 提供简单的调用接口
"""
import logging
from typing import Optional
from app.config import settings
from app.services.ai.base import AIProviderConfig
from app.services.ai.providers import OpenAIProvider

logger = logging.getLogger(__name__)


class AIService:
    """AI服务包装器"""
    
    def __init__(self):
        self._provider = None
        self._init_provider()
    
    def _init_provider(self):
        """初始化AI Provider"""
        provider_type = settings.ai_default_provider
        
        if provider_type == "zhipu":
            # 智谱AI
            if not settings.zhipu_api_key:
                logger.warning("Zhipu API key not configured")
                return
            
            self._provider = OpenAIProvider(AIProviderConfig(
                provider_type="openai",
                api_key=settings.zhipu_api_key,
                base_url=settings.zhipu_base_url,
                model=settings.zhipu_model
            ))
        else:
            # OpenAI
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not configured")
                return
            
            self._provider = OpenAIProvider(AIProviderConfig(
                provider_type="openai",
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_model
            ))
    
    async def call(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        调用AI服务
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数
            **kwargs: 其他参数
        
        Returns:
            AI响应文本
        """
        if not self._provider:
            raise Exception("AI provider not configured. Please set API key in .env file.")
        
        try:
            response = await self._provider.call(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            # 提取响应文本
            if isinstance(response, dict):
                if "choices" in response:
                    return response["choices"][0]["message"]["content"]
                else:
                    return str(response)
            else:
                return response
                
        except Exception as e:
            logger.error(f"AI service call failed: {e}")
            raise


# 全局实例
_ai_service = None


def get_ai_service() -> AIService:
    """获取AI服务实例"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
