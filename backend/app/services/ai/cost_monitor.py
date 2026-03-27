"""
AI Cost Monitoring Service
Tracks AI request costs and enforces daily limits
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.ai_config import AIRequestLog


class CostMonitor:
    """AI cost monitoring and daily limit enforcement"""

    # Default costs per million tokens (if not provided by provider)
    DEFAULT_COSTS = {
        "input": 1.0,  # $1 per million input tokens
        "output": 2.0  # $2 per million output tokens
    }

    def __init__(self, db: Session, daily_limit_usd: Optional[float] = None):
        """
        Initialize cost monitor

        Args:
            db: Database session
            daily_limit_usd: Daily cost limit in USD (uses config default if not specified)
        """
        from app.config import settings

        self.db = db
        self.daily_limit_usd = daily_limit_usd or settings.ai_daily_cost_limit

    async def check_daily_limit(self, provider: Optional[str] = None) -> tuple[bool, float]:
        """
        Check if daily cost limit has been exceeded

        Args:
            provider: Optional provider to check (checks all if not specified)

        Returns:
            tuple: (under_limit, current_cost_usd)
        """
        # Get today's start
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Build query
        query = self.db.query(func.coalesce(func.sum(AIRequestLog.cost_usd), 0)).filter(
            AIRequestLog.created_at >= today_start,
            AIRequestLog.status == "success"
        )

        if provider:
            query = query.filter(AIRequestLog.provider == provider)

        # Get total cost
        total_cost = query.scalar() or 0.0

        return total_cost < self.daily_limit_usd, total_cost

    async def log_request(
        self,
        provider: str,
        model: str,
        request_type: str,
        status: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        cost_usd: Optional[float] = None,
        latency_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        request_hash: Optional[str] = None
    ) -> AIRequestLog:
        """
        Log AI request

        Args:
            provider: Provider type
            model: Model name
            request_type: Type of request (element_match, testcase_gen, etc.)
            status: Request status (success, error, timeout)
            input_tokens: Input tokens consumed
            output_tokens: Output tokens consumed
            cost_usd: Cost in USD
            latency_ms: Request latency in milliseconds
            error_message: Error message if failed
            request_hash: Request hash for cache lookup

        Returns:
            Created AIRequestLog entry
        """
        log_entry = AIRequestLog(
            provider=provider,
            model=model,
            request_type=request_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            status=status,
            error_message=error_message,
            request_hash=request_hash
        )

        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)

        return log_entry

    def calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate cost based on provider and model

        Args:
            provider: Provider type
            model: Model name
            input_tokens: Input tokens
            output_tokens: Output tokens

        Returns:
            Cost in USD
        """
        # Get costs per million tokens
        costs = self._get_model_costs(provider, model)

        # Calculate cost
        cost = (input_tokens * costs["input"] / 1_000_000) + \
               (output_tokens * costs["output"] / 1_000_000)

        return round(cost, 6)

    def _get_model_costs(self, provider: str, model: str) -> dict:
        """Get cost per million tokens for a model"""
        # Model-specific costs
        model_costs = {
            "openai": {
                "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
                "gpt-4": {"input": 30, "output": 60},
                "gpt-4-turbo": {"input": 10, "output": 30},
                "gpt-4o": {"input": 5, "output": 15},
            },
            "zhipu": {
                "glm-4": {"input": 1.0, "output": 1.0},
                "glm-4-plus": {"input": 5.0, "output": 5.0},
                "glm-4-0520": {"input": 1.0, "output": 1.0},
            }
        }

        # Try to get specific costs
        if provider in model_costs and model in model_costs[provider]:
            return model_costs[provider][model]

        # Use default costs
        return self.DEFAULT_COSTS

    def get_daily_stats(self, provider: Optional[str] = None) -> dict:
        """
        Get daily statistics

        Args:
            provider: Optional provider filter

        Returns:
            Dict with daily stats
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Build base query
        query = self.db.query(
            func.count(AIRequestLog.id).label('total_requests'),
            func.sum(AIRequestLog.input_tokens).label('total_input_tokens'),
            func.sum(AIRequestLog.output_tokens).label('total_output_tokens'),
            func.sum(AIRequestLog.cost_usd).label('total_cost'),
            func.avg(AIRequestLog.latency_ms).label('avg_latency')
        ).filter(
            AIRequestLog.created_at >= today_start
        )

        if provider:
            query = query.filter(AIRequestLog.provider == provider)

        result = query.first()

        return {
            "date": today_start.date().isoformat(),
            "total_requests": result.total_requests or 0,
            "total_input_tokens": result.total_input_tokens or 0,
            "total_output_tokens": result.total_output_tokens or 0,
            "total_tokens": (result.total_input_tokens or 0) + (result.total_output_tokens or 0),
            "total_cost_usd": float(result.total_cost or 0),
            "avg_latency_ms": float(result.avg_latency or 0),
            "daily_limit_usd": self.daily_limit_usd,
            "remaining_budget_usd": max(0, self.daily_limit_usd - float(result.total_cost or 0))
        }

    def get_recent_logs(
        self,
        limit: int = 100,
        provider: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[AIRequestLog]:
        """
        Get recent request logs

        Args:
            limit: Maximum number of logs
            provider: Optional provider filter
            status: Optional status filter

        Returns:
            List of AIRequestLog entries
        """
        query = self.db.query(AIRequestLog)

        if provider:
            query = query.filter(AIRequestLog.provider == provider)

        if status:
            query = query.filter(AIRequestLog.status == status)

        return query.order_by(AIRequestLog.created_at.desc()).limit(limit).all()
