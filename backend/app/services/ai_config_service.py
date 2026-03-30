"""
AI配置服务 - 统一入口（向后兼容）
"""
from app.services.ai.ai_service import get_ai_service, AIService

# 导出
get_ai_config_service = get_ai_service

__all__ = ['get_ai_config_service', 'get_ai_service', 'AIService']
