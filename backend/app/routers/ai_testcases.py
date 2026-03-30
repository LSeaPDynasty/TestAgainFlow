"""
AI辅助用例管理接口
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db_session
from app.services.ai.testcase_description_service import testcase_description_service
from app.utils.response import ok, error

router = APIRouter(prefix="/ai/testcases", tags=["ai-testcases"])


class GenerateTestcaseDescriptionRequest(BaseModel):
    testcase_name: str
    flow_names: List[str]
    priority: str
    tags: List[str]


@router.post("/generate-description", response_model=object)
async def generate_testcase_description(
    request: GenerateTestcaseDescriptionRequest,
    db: Session = Depends(get_db_session)
):
    """AI生成用例描述"""
    try:
        description = await testcase_description_service.generate_description(
            testcase_name=request.testcase_name,
            flow_names=request.flow_names,
            priority=request.priority,
            tags=request.tags
        )
        return ok(data={"description": description})
    except Exception as e:
        return error(code=5000, message=f"生成描述失败: {str(e)}")
