"""
AI Provider base classes and interfaces
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class ProviderType(str, Enum):
    """AI Provider types"""
    OPENAI = "openai"
    ZHIPU = "zhipu"
    CUSTOM = "custom"


@dataclass
class AIMessage:
    """AI Chat message"""
    role: str  # 'system', 'user', 'assistant'
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class AIResponse:
    """AI Response wrapper"""
    content: str
    tool_calls: Optional[List[Dict]] = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    raw_response: Optional[Dict] = None


@dataclass
class AIProviderConfig:
    """AI Provider configuration"""
    provider_type: str
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    timeout: int = 30
    max_retries: int = 3
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIRequestStats:
    """AI Request statistics"""
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[int] = None


class AIProviderBase(ABC):
    """
    Base class for AI providers
    All providers must implement these methods
    """

    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.provider_type = config.provider_type

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict]] = None,
        response_format: Optional[Dict] = None
    ) -> tuple[AIResponse, AIRequestStats]:
        """
        Perform chat completion

        Returns:
            tuple: (AIResponse, AIRequestStats)
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the provider connection is working"""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the provider configuration"""
        pass

    def _calculate_stats(
        self,
        start_time: float,
        usage: Optional[Dict] = None,
        cost_per_input: float = 0.000001,
        cost_per_output: float = 0.000002
    ) -> AIRequestStats:
        """Calculate request statistics"""
        import time

        latency_ms = int((time.time() - start_time) * 1000)
        input_tokens = usage.get('prompt_tokens') if usage else None
        output_tokens = usage.get('completion_tokens') if usage else None

        cost_usd = None
        if input_tokens and output_tokens:
            cost_usd = (input_tokens * cost_per_input) + (output_tokens * cost_per_output)

        return AIRequestStats(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=usage.get('total_tokens') if usage else None,
            cost_usd=cost_usd,
            latency_ms=latency_ms
        )

    def _serialize_messages(self, messages: List[AIMessage]) -> List[Dict]:
        """Serialize AIMessage objects to dicts"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                **({"tool_calls": msg.tool_calls} if msg.tool_calls else {}),
                **({"tool_call_id": msg.tool_call_id} if msg.tool_call_id else {})
            }
            for msg in messages
        ]
