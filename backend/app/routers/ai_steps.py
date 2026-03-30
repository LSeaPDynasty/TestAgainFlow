"""
AI辅助步骤管理接口
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db_session
from app.services.ai.step_description_service import step_description_service
from app.utils.response import ok, error

router = APIRouter(prefix="/ai/steps", tags=["ai-steps"])


class GenerateStepDescriptionRequest(BaseModel):
    """生成步骤描述请求"""
    step_name: str
    action_type: str
    element_name: Optional[str] = None
    element_description: Optional[str] = None


@router.post("/generate-description", response_model=object)
async def generate_step_description(
    request: GenerateStepDescriptionRequest,
    db: Session = Depends(get_db_session)
):
    """AI生成步骤描述"""
    try:
        description = await step_description_service.generate_description(
            step_name=request.step_name,
            action_type=request.action_type,
            element_name=request.element_name,
            element_description=request.element_description
        )
        return ok(data={"description": description})
    except Exception as e:
        return error(code=5000, message=f"生成描述失败: {str(e)}")
