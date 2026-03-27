"""
OpenAI-compatible AI Provider
Supports OpenAI API and Zhipu AI compatible API format
"""
import asyncio
import time
from typing import Optional
import httpx

from ..base import (
    AIProviderBase,
    AIProviderConfig,
    AIMessage,
    AIResponse,
    AIRequestStats
)


class OpenAIProvider(AIProviderBase):
    """
    OpenAI-compatible provider
    Works with OpenAI API and Zhipu AI (when using compatible endpoint)
    """

    # Token costs per million tokens (approximate)
    COSTS = {
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "gpt-4": {"input": 30, "output": 60},
        "gpt-4-turbo": {"input": 10, "output": 30},
        "gpt-4o": {"input": 5, "output": 15},
        "glm-4": {"input": 1.0, "output": 1.0},
        "glm-4-plus": {"input": 5.0, "output": 5.0},
    }

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.openai.com/v1"
        self.api_key = config.api_key
        self.model = config.model
        self.timeout = config.timeout
        self.max_retries = config.max_retries

        # Initialize HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=self.timeout
        )

    async def chat_completion(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[list] = None,
        response_format: Optional[dict] = None
    ) -> tuple[AIResponse, AIRequestStats]:
        """Perform chat completion request"""

        start_time = time.time()

        # Build request payload
        payload = {
            "model": self.model,
            "messages": self._serialize_messages(messages),
            "temperature": temperature
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if tools:
            payload["tools"] = tools

        if response_format:
            payload["response_format"] = response_format

        # Execute request with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post("/chat/completions", json=payload)
                response.raise_for_status()

                data = response.json()
                choice = data["choices"][0]
                message = choice["message"]

                # Build response
                ai_response = AIResponse(
                    content=message.get("content", ""),
                    tool_calls=message.get("tool_calls"),
                    usage=data.get("usage"),
                    model=data.get("model"),
                    raw_response=data
                )

                # Calculate stats
                costs = self.COSTS.get(self.model, {"input": 1.0, "output": 1.0})
                stats = self._calculate_stats(
                    start_time,
                    data.get("usage"),
                    cost_per_input=costs["input"] / 1_000_000,
                    cost_per_output=costs["output"] / 1_000_000
                )

                return ai_response, stats

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code < 500 or attempt == self.max_retries - 1:
                    # Client error or last attempt, raise
                    raise Exception(f"API request failed: {e.response.status_code} - {e.response.text}")

                # Server error, retry after delay
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    raise

                await asyncio.sleep(2 ** attempt)

        # Should not reach here, but just in case
        raise Exception(f"Request failed after {self.max_retries} retries: {last_error}")

    async def test_connection(self) -> bool:
        """Test the API connection"""
        try:
            messages = [AIMessage(role="user", content="Hello")]
            response, stats = await self.chat_completion(messages, max_tokens=5)
            return bool(response.content)
        except Exception:
            return False

    def validate_config(self) -> bool:
        """Validate the configuration"""
        return bool(self.api_key and self.model)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
