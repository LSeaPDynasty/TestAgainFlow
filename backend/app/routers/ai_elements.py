"""
AI辅助元素管理接口
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db_session, require_auth
from app.services.ai.element_description_service import element_description_service
from app.utils.response import ok, error

router = APIRouter(prefix="/ai/elements", tags=["ai-elements"])


class GenerateDescriptionRequest(BaseModel):
    """生成描述请求"""
    element_name: str
    screen_name: str
    locators: list[dict]


class BatchGenerateDescriptionRequest(BaseModel):
    """批量生成描述请求"""
    element_ids: list[int]


@router.post("/generate-description", response_model=object)
async def generate_element_description(
    request: GenerateDescriptionRequest,
    db: Session = Depends(get_db_session)
    # auth: dict = Depends(require_auth)  # 暂时禁用认证，方便测试
):
    """
    AI生成元素描述
    
    根据元素信息生成规范的描述文本
    """
    try:
        description = await element_description_service.generate_description(
            element_name=request.element_name,
            screen_name=request.screen_name,
            locators=request.locators
        )
        return ok(data={"description": description})
    except Exception as e:
        return error(code=5000, message=f"生成描述失败: {str(e)}")


@router.post("/batch-generate-description", response_model=object)
async def batch_generate_element_description(
    request: BatchGenerateDescriptionRequest,
    db: Session = Depends(get_db_session)
    # auth: dict = Depends(require_auth)  # 暂时禁用认证，方便测试
):
    """
    批量生成元素描述
    
    为指定的元素批量生成描述
    """
    try:
        from app.models.element import Element
        from app.models.screen import Screen
        
        # 查询元素信息
        elements = db.query(Element).filter(
            Element.id.in_(request.element_ids)
        ).all()
        
        if not elements:
            return error(code=4004, message="未找到指定的元素")
        
        # 构建请求数据
        element_data = []
        for elem in elements:
            screen = db.query(Screen).filter(Screen.id == elem.screen_id).first()
            element_data.append({
                'id': elem.id,
                'name': elem.name,
                'screen_name': screen.name if screen else '',
                'locators': [
                    {'type': loc.type, 'value': loc.value}
                    for loc in elem.locators
                ]
            })
        
        # 批量生成
        descriptions = await element_description_service.batch_generate(element_data)
        
        # 更新数据库
        for elem_id, desc in descriptions.items():
            elem = next((e for e in elements if e.id == elem_id), None)
            if elem:
                elem.description = desc
        
        db.commit()
        
        return ok(data={
            "updated_count": len(descriptions),
            "descriptions": descriptions
        })
    except Exception as e:
        db.rollback()
        return error(code=5000, message=f"批量生成失败: {str(e)}")
