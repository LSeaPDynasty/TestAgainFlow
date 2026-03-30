"""
AI辅助流程管理接口
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from app.dependencies import get_db_session
from app.services.ai.flow_description_service import flow_description_service
from app.utils.response import ok, error

router = APIRouter(prefix="/ai/flows", tags=["ai-flows"])


class GenerateFlowDescriptionRequest(BaseModel):
    flow_name: str
    flow_type: str
    step_names: List[str]
    purpose: Optional[str] = None


@router.post("/generate-description", response_model=object)
async def generate_flow_description(
    request: GenerateFlowDescriptionRequest,
    db: Session = Depends(get_db_session)
):
    """AI生成流程描述"""
    try:
        description = await flow_description_service.generate_description(
            flow_name=request.flow_name,
            flow_type=request.flow_type,
            step_names=request.step_names,
            purpose=request.purpose
        )
        return ok(data={"description": description})
    except Exception as e:
        return error(code=5000, message=f"生成描述失败: {str(e)}")
