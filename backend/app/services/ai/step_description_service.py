"""
AI辅助步骤描述生成服务
"""
import logging
from typing import Optional
from .ai_service import get_ai_service

logger = logging.getLogger(__name__)


class StepDescriptionService:
    """步骤描述生成服务"""
    
    def __init__(self):
        self.ai_service = get_ai_service()
    
    async def generate_description(
        self,
        step_name: str,
        action_type: str,
        element_name: Optional[str] = None,
        element_description: Optional[str] = None,
        context: Optional[dict] = None
    ) -> str:
        """生成步骤描述"""
        element_info = ""
        if element_description:
            element_info = f"，目标元素：{element_description}"
        elif element_name:
            element_info = f"，目标元素：{element_name}"
        
        action_map = {
            "click": "点击",
            "input": "输入",
            "swipe": "滑动",
            "wait_element": "等待",
            "assert_text": "断言",
            "screenshot": "截图"
        }
        action_cn = action_map.get(action_type, action_type)
        
        prompt = f"""为以下Android自动化测试步骤生成一个简洁、准确的描述：

步骤名称：{step_name}
操作类型：{action_type}（{action_cn}）{element_info}

要求：
1. 描述要简洁（10-25字）
2. 说明操作类型和目标
3. 使用动词开头（如"点击"、"输入"、"等待"）
4. 不要包含技术细节

示例格式：
- "点击登录按钮"
- "输入用户名"
- "等待首页加载完成"
- "断言显示成功提示"

请只返回描述文本，不要其他内容。"""
        
        try:
            from app.services.ai.base import AIMessage
            response, stats = await self.ai_service._provider.chat_completion(
                messages=[AIMessage(role="user", content=prompt)],
                max_tokens=100,
                temperature=0.3
            )
            
            description = response.content.strip().strip('"\'')
            logger.info(f"Generated description for step {step_name}: {description}")
            return description
            
        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            return self._generate_fallback_description(step_name, action_type, element_name)
    
    def _generate_fallback_description(self, step_name: str, action_type: str, element_name: Optional[str]) -> str:
        """降级方案"""
        action_map = {
            "click": "点击",
            "input": "输入",
            "swipe": "滑动",
            "wait_element": "等待",
            "assert_text": "断言",
            "screenshot": "截图"
        }
        action_cn = action_map.get(action_type, action_type)
        
        if element_name:
            return f"{action_cn}{element_name}"
        return f"{action_cn}操作"


step_description_service = StepDescriptionService()
