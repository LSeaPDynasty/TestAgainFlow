"""
Custom HTTP Provider
Supports custom HTTP endpoints with OpenAI-compatible request/response format
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


class CustomHTTPProvider(AIProviderBase):
    """
    Custom HTTP provider for generic OpenAI-compatible endpoints
    Useful for self-hosted models or other AI services
    """

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url
        self.api_key = config.api_key
        self.model = config.model
        self.timeout = config.timeout
        self.max_retries = config.max_retries

        # Get custom headers from extra_params
        self.custom_headers = config.extra_params.get("headers", {})

        # Get cost configuration from extra_params
        self.cost_per_input = config.extra_params.get("cost_per_input", 1.0) / 1_000_000
        self.cost_per_output = config.extra_params.get("cost_per_output", 1.0) / 1_000_000

        # Initialize HTTP client
        headers = {
            "Content-Type": "application/json",
            **self.custom_headers
        }

        if self.api_key:
            # Default to Bearer token if not specified
            auth_header = config.extra_params.get("auth_header", "Authorization")
            auth_format = config.extra_params.get("auth_format", "Bearer {key}")
            headers[auth_header] = auth_format.format(key=self.api_key)

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
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

        # Get custom endpoint path from extra_params
        endpoint = self.config.extra_params.get("endpoint", "/chat/completions")

        # Execute request with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(endpoint, json=payload)
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
                stats = self._calculate_stats(
                    start_time,
                    data.get("usage"),
                    cost_per_input=self.cost_per_input,
                    cost_per_output=self.cost_per_output
                )

                return ai_response, stats

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code < 500 or attempt == self.max_retries - 1:
                    raise Exception(f"Custom API request failed: {e.response.status_code} - {e.response.text}")

                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    raise

                await asyncio.sleep(2 ** attempt)

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
        return bool(self.base_url and self.model)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
