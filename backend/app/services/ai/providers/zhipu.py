"""
Zhipu AI Native Provider
Uses the Zhipu AI SDK for direct API access
"""
import asyncio
import time
import jwt
from typing import Optional
import httpx

from ..base import (
    AIProviderBase,
    AIProviderConfig,
    AIMessage,
    AIResponse,
    AIRequestStats
)


class ZhipuProvider(AIProviderBase):
    """
    Zhipu AI native provider
    Uses JWT-based authentication for Zhipu AI platform
    """

    # Token costs per million tokens (approximate)
    COSTS = {
        "glm-4": {"input": 1.0, "output": 1.0},
        "glm-4-plus": {"input": 5.0, "output": 5.0},
        "glm-4-0520": {"input": 1.0, "output": 1.0},
        "glm-4-air": {"input": 0.5, "output": 0.5},
    }

    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model or "glm-4"
        self.base_url = config.base_url or "https://open.bigmodel.cn/api/paas/v4"
        self.timeout = config.timeout
        self.max_retries = config.max_retries

        # Parse API key (format: id.secret)
        self.api_key_id, self.api_key_secret = self._parse_api_key()

    def _parse_api_key(self) -> tuple:
        """Parse Zhipu API key format"""
        try:
            parts = self.api_key.split(".")
            if len(parts) != 2:
                raise ValueError("Invalid Zhipu API key format")
            return parts[0], parts[1]
        except Exception:
            return "", ""

    def _generate_token(self, expire_time: int = 3600) -> str:
        """Generate JWT token for Zhipu API"""
        try:
            payload = {
                "api_key": self.api_key_id,
                "exp": time.time() + expire_time,
                "timestamp": time.time()
            }
            token = jwt.encode(payload, self.api_key_secret, algorithm="HS256")
            return token
        except Exception:
            # Fallback to using API key directly
            return self.api_key

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

        # Generate token
        token = self._generate_token()

        # Execute request with retries
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=self.timeout
        ) as client:
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    response = await client.post("/chat/completions", json=payload)
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
                        raise Exception(f"Zhipu API request failed: {e.response.status_code} - {e.response.text}")

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
        return bool(self.api_key and "." in self.api_key)
