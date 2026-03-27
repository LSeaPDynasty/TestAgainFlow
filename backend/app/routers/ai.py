"""
AI Router - AI-powered test automation endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Any

from app.database import get_db
from app.schemas.ai import (
    ElementSuggestRequest,
    ElementSuggestResponse,
    TestcaseGenerateRequest,
    TestcaseGenerateResponse,
    AIConfigCreate,
    AIConfigUpdate,
    AIConfigResponse,
    AIConfigTestRequest,
    AIConfigTestResponse,
    DailyStatsResponse
)
from app.schemas.common import ApiResponse
from app.utils.response import ok, error
from app.services.ai.element_matcher import ElementMatcher
from app.services.ai.testcase_generator import TestcaseGenerator
from app.services.ai.config_service import AIConfigService
from app.services.ai.cost_monitor import CostMonitor

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/elements/suggest", response_model=ApiResponse)
async def suggest_elements(
    request: ElementSuggestRequest,
    db: Session = Depends(get_db)
):
    """
    Get AI-powered element suggestions from DOM element

    Analyzes DOM element and suggests:
    - Similar existing elements to reuse
    - New element creation with suggested name and locators
    """
    try:
        matcher = ElementMatcher(db)

        # Convert DOMElement to dict
        dom_element_dict = request.dom_element.model_dump(by_alias=True)

        # Find similar elements
        result = await matcher.find_similar_elements(
            dom_element=dom_element_dict,
            screen_id=request.screen_id,
            project_id=request.project_id,
            threshold=request.threshold
        )

        return ok(data=result)

    except Exception as e:
        return error(message=f"Element suggestion failed: {str(e)}")


@router.post("/testcases/generate", response_model=ApiResponse)
async def generate_testcase(
    request: TestcaseGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate test case plan from JSON description

    Analyzes test case requirements and generates:
    - Optimal test case structure
    - Resource reuse recommendations
    - Missing resource identification
    """
    try:
        generator = TestcaseGenerator(db)

        # Check daily limit first
        from app.config import settings
        cost_monitor = CostMonitor(db, daily_limit_usd=settings.ai_daily_cost_limit)
        under_limit, current_cost = await cost_monitor.check_daily_limit()

        if not under_limit:
            return error(
                message=f"Daily AI cost limit exceeded. Current cost: ${current_cost:.2f}",
                code="daily_limit_exceeded"
            )

        # Generate test case plan
        result = await generator.generate_from_json(
            json_data=request.json_data,
            project_id=request.project_id
        )

        return ok(data=result)

    except Exception as e:
        return error(message=f"Test case generation failed: {str(e)}")


@router.post("/steps/generate", response_model=ApiResponse)
async def generate_step(
    step_description: str,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Generate a single test step from natural language description

    Creates a step configuration with appropriate type, element, and parameters
    """
    try:
        generator = TestcaseGenerator(db)

        # Check daily limit
        from app.config import settings
        cost_monitor = CostMonitor(db, daily_limit_usd=settings.ai_daily_cost_limit)
        under_limit, _ = await cost_monitor.check_daily_limit()

        if not under_limit:
            return error(
                message="Daily AI cost limit exceeded",
                code="daily_limit_exceeded"
            )

        # Generate step
        result = await generator.generate_step(
            step_description=step_description,
            project_id=project_id
        )

        return ok(data=result)

    except Exception as e:
        return error(message=f"Step generation failed: {str(e)}")


# AI Configuration endpoints
@router.get("/config", response_model=ApiResponse)
async def list_ai_configs(
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all AI configurations"""
    try:
        config_service = AIConfigService(db)
        configs = config_service.list_configs(active_only=active_only)

        # Convert to safe dict format (masked API keys)
        result = [config_service.to_dict_safe(c) for c in configs]

        return ok(data=result)

    except Exception as e:
        return error(message=f"Failed to list configs: {str(e)}")


@router.get("/config/{config_id}", response_model=ApiResponse)
async def get_ai_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Get specific AI configuration"""
    try:
        config_service = AIConfigService(db)
        config = config_service.get_config_by_id(config_id)

        if not config:
            return error(message="AI config not found", code="not_found")

        return ok(data=config_service.to_dict_safe(config))

    except Exception as e:
        return error(message=f"Failed to get config: {str(e)}")


@router.post("/config", response_model=ApiResponse)
async def create_ai_config(
    request: AIConfigCreate,
    db: Session = Depends(get_db)
):
    """Create new AI configuration"""
    try:
        config_service = AIConfigService(db)

        # Check if name already exists
        existing = config_service.list_configs()
        if any(c.name == request.name for c in existing):
            return error(message="Config with this name already exists", code="duplicate_name")

        # Create config
        config = config_service.create_config(
            provider=request.provider,
            name=request.name,
            config_data=request.config_data,
            priority=request.priority,
            is_active=request.is_active
        )

        return ok(data=config_service.to_dict_safe(config), message="AI config created successfully")

    except Exception as e:
        return error(message=f"Failed to create config: {str(e)}")


@router.put("/config/{config_id}", response_model=ApiResponse)
async def update_ai_config(
    config_id: int,
    request: AIConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update AI configuration"""
    try:
        config_service = AIConfigService(db)

        # Prepare update data
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.config_data is not None:
            update_data["config_data"] = request.config_data
        if request.priority is not None:
            update_data["priority"] = request.priority
        if request.is_active is not None:
            update_data["is_active"] = request.is_active

        # Update config
        config = config_service.update_config(config_id, **update_data)

        if not config:
            return error(message="AI config not found", code="not_found")

        return ok(data=config_service.to_dict_safe(config), message="AI config updated successfully")

    except Exception as e:
        return error(message=f"Failed to update config: {str(e)}")


@router.delete("/config/{config_id}", response_model=ApiResponse)
async def delete_ai_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Delete AI configuration"""
    try:
        config_service = AIConfigService(db)
        success = config_service.delete_config(config_id)

        if not success:
            return error(message="AI config not found", code="not_found")

        return ok(message="AI config deleted successfully")

    except Exception as e:
        return error(message=f"Failed to delete config: {str(e)}")


@router.post("/config/test", response_model=ApiResponse)
async def test_ai_config(
    request: AIConfigTestRequest,
    db: Session = Depends(get_db)
):
    """Test AI configuration by making a simple request"""
    import time

    try:
        config_service = AIConfigService(db)

        # Create provider config
        from app.services.ai.base import AIProviderConfig
        provider_config = AIProviderConfig(
            provider_type=request.provider,
            **request.config_data
        )

        # Create provider
        provider = config_service._create_provider(provider_config)

        # Test connection
        start_time = time.time()
        success = await provider.test_connection()
        latency_ms = int((time.time() - start_time) * 1000)

        if success:
            return ok(data={
                "success": True,
                "latency_ms": latency_ms
            }, message="AI config test successful")
        else:
            return error(message="AI config test failed", code="test_failed")

    except Exception as e:
        return error(message=f"AI config test failed: {str(e)}")


@router.get("/config/active", response_model=ApiResponse)
async def get_active_config(
    profile_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get currently active AI configuration"""
    try:
        config_service = AIConfigService(db)
        config = config_service.get_active_config(profile_id)

        if not config:
            return ok(data=None, message="No active AI config found")

        return ok(data=config_service.to_dict_safe(config))

    except Exception as e:
        return error(message=f"Failed to get active config: {str(e)}")


# Monitoring endpoints
@router.get("/stats/daily", response_model=ApiResponse)
async def get_daily_stats(
    provider: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get daily AI usage statistics"""
    try:
        from app.config import settings
        cost_monitor = CostMonitor(db, daily_limit_usd=settings.ai_daily_cost_limit)
        stats = cost_monitor.get_daily_stats(provider=provider)

        return ok(data=stats)

    except Exception as e:
        return error(message=f"Failed to get daily stats: {str(e)}")


@router.get("/logs/recent", response_model=ApiResponse)
async def get_recent_logs(
    limit: int = 100,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get recent AI request logs"""
    try:
        from app.config import settings
        cost_monitor = CostMonitor(db, daily_limit_usd=settings.ai_daily_cost_limit)
        logs = cost_monitor.get_recent_logs(limit=limit, provider=provider, status=status)

        # Convert to dict
        result = [
            {
                "id": log.id,
                "provider": log.provider,
                "model": log.model,
                "request_type": log.request_type,
                "input_tokens": log.input_tokens,
                "output_tokens": log.output_tokens,
                "cost_usd": log.cost_usd,
                "latency_ms": log.latency_ms,
                "status": log.status,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]

        return ok(data=result)

    except Exception as e:
        return error(message=f"Failed to get recent logs: {str(e)}")


@router.post("/batch-import/correct", response_model=ApiResponse)
async def correct_batch_import_json(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """使用AI修正批量导入的JSON格式"""
    try:
        from app.services.ai.batch_import_corrector import BatchImportCorrector

        corrector = BatchImportCorrector(db)
        result = await corrector.correct_and_validate(
            json_data=request.get("json_data"),
            project_id=request.get("project_id")
        )

        return ok(data=result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return error(code="server_error", message=f"批量导入修正失败: {str(e)}")
