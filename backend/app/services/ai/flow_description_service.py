"""
AI辅助流程描述生成服务
"""
import logging
from typing import Optional, List
from .ai_service import get_ai_service

logger = logging.getLogger(__name__)


class FlowDescriptionService:
    """流程描述生成服务"""
    
    def __init__(self):
        self.ai_service = get_ai_service()
    
    async def generate_description(
        self,
        flow_name: str,
        flow_type: str,
        step_names: List[str],
        purpose: Optional[str] = None,
        context: Optional[dict] = None
    ) -> str:
        """生成流程描述"""
        steps_info = "、".join(step_names[:5])
        if len(step_names) > 5:
            steps_info += f"等{len(step_names)}个步骤"
        
        prompt = f"""为以下Android自动化测试流程生成一个简洁、准确的描述：

流程名称：{flow_name}
流程类型：{flow_type}
包含步骤：{steps_info}
流程目的：{purpose or '未指定'}

要求：
1. 描述要简洁（15-35字）
2. 说明流程的主要功能
3. 提及包含的主要操作
4. 使用"用于..."的格式

请只返回描述文本，不要其他内容。"""
        
        try:
            from app.services.ai.base import AIMessage
            response, stats = await self.ai_service._provider.chat_completion(
                messages=[AIMessage(role="user", content=prompt)],
                max_tokens=150,
                temperature=0.3
            )
            
            description = response.content.strip().strip('"\'')
            logger.info(f"Generated description for flow {flow_name}: {description}")
            return description
            
        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            return f"{flow_name}流程"


flow_description_service = FlowDescriptionService()
