"""
AI辅助用例描述生成服务
"""
import logging
from typing import List, Optional
from .ai_service import get_ai_service

logger = logging.getLogger(__name__)


class TestcaseDescriptionService:
    """用例描述生成服务"""
    
    def __init__(self):
        self.ai_service = get_ai_service()
    
    async def generate_description(
        self,
        testcase_name: str,
        flow_names: List[str],
        priority: str,
        tags: List[str],
        context: Optional[dict] = None
    ) -> str:
        """生成用例描述"""
        flows_info = "、".join(flow_names[:3])
        if len(flow_names) > 3:
            flows_info += f"等{len(flow_names)}个流程"
        
        prompt = f"""为以下Android自动化测试用例生成一个简洁、准确的描述：

用例名称：{testcase_name}
包含流程：{flows_info}
优先级：{priority}
标签：{", ".join(tags) if tags else "无"}

要求：
1. 描述要简洁（20-40字）
2. 说明测试的功能点和验证内容
3. 使用"验证..."或"测试..."的格式

请只返回描述文本，不要其他内容。"""
        
        try:
            from app.services.ai.base import AIMessage
            response, stats = await self.ai_service._provider.chat_completion(
                messages=[AIMessage(role="user", content=prompt)],
                max_tokens=150,
                temperature=0.3
            )
            
            description = response.content.strip().strip('"\'')
            logger.info(f"Generated description for testcase {testcase_name}: {description}")
            return description
            
        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            return f"{priority}测试用例：{testcase_name}"


testcase_description_service = TestcaseDescriptionService()
