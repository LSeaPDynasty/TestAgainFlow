"""
AI Configuration and logging models
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, JSON, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class AIConfig(BaseModel):
    """AI Provider configuration model"""
    __tablename__ = 'ai_configs'

    provider = Column(String(50), nullable=False, comment='Provider type: openai, zhipu, custom')
    name = Column(String(100), nullable=False, unique=True, comment='Configuration name')
    config = Column(JSON, nullable=False, comment='Encrypted configuration including api_key, base_url, model')
    is_active = Column(Boolean, default=True, nullable=False, comment='Whether this configuration is active')
    priority = Column(Integer, default=1, nullable=False, comment='Priority for config selection')

    def __repr__(self):
        return f"<AIConfig(id={self.id}, name='{self.name}', provider='{self.provider}')>"


class AIRequestLog(BaseModel):
    """AI request logging model for monitoring and cost tracking"""
    __tablename__ = 'ai_request_logs'

    provider = Column(String(50), nullable=False, comment='Provider type')
    model = Column(String(100), nullable=False, comment='Model name used')
    request_type = Column(String(50), nullable=False, comment='Request type: element_match, testcase_gen, etc.')
    input_tokens = Column(Integer, nullable=True, comment='Input tokens consumed')
    output_tokens = Column(Integer, nullable=True, comment='Output tokens consumed')
    cost_usd = Column(Float(10), nullable=True, comment='Cost in USD')
    latency_ms = Column(Integer, nullable=True, comment='Request latency in milliseconds')
    status = Column(String(20), nullable=False, comment='Request status: success, error, timeout')
    error_message = Column(Text, nullable=True, comment='Error message if failed')
    request_hash = Column(String(64), nullable=True, comment='Hash of request for cache lookup')

    def __repr__(self):
        return f"<AIRequestLog(id={self.id}, provider='{self.provider}', status='{self.status}')>"


class AICache(BaseModel):
    """AI response caching model"""
    __tablename__ = 'ai_cache'

    request_hash = Column(String(64), unique=True, nullable=False, comment='Hash of request payload')
    response_data = Column(JSON, nullable=False, comment='Cached response data')
    expires_at = Column(DateTime, nullable=False, comment='Cache expiration time')

    def __repr__(self):
        return f"<AICache(id={self.id}, expires_at='{self.expires_at}')>"
