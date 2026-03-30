"""
AI辅助元素描述生成服务
根据元素信息生成规范的描述
"""
import logging
from typing import Optional
from .ai_service import get_ai_service

logger = logging.getLogger(__name__)


class ElementDescriptionService:
    """元素描述生成服务"""
    
    def __init__(self):
        self.ai_service = get_ai_service()
    
    async def generate_description(
        self,
        element_name: str,
        screen_name: str,
        locators: list[dict],
        context: Optional[dict] = None
    ) -> str:
        """
        生成元素描述
        
        Args:
            element_name: 元素名称
            screen_name: 所属界面
            locators: 定位符列表
            context: 额外上下文（如页面截图、XML等）
        
        Returns:
            生成的描述文本
        """
        # 构建prompt
        locator_info = "\n".join([
            f"- {loc['type']}: {loc['value']}"
            for loc in locators
        ])
        
        prompt = f"""为以下Android UI元素生成一个简洁、准确的描述：

元素名称：{element_name}
所属界面：{screen_name}
定位符：
{locator_info}

要求：
1. 描述要简洁（15-30字）
2. 说明元素的类型（按钮/输入框/文本等）
3. 说明元素的用途或功能
4. 不要包含定位符技术细节

示例格式：
- "登录表单的提交按钮"
- "用户名输入框"
- "显示错误提示的文本标签"

请只返回描述文本，不要其他内容。"""
        
        try:
            # 调用AI服务
            response = await self.ai_service.call(
                prompt=prompt,
                max_tokens=100,
                temperature=0.3  # 低温度，保证稳定性
            )
            
            description = response.strip().strip('"\'')
            logger.info(f"Generated description for {element_name}: {description}")
            return description
            
        except Exception as e:
            logger.error(f"Failed to generate description: {e}")
            # 降级：生成简单描述
            return self._generate_fallback_description(element_name, locators)
    
    def _generate_fallback_description(self, element_name: str, locators: list) -> str:
        """降级方案：基于规则生成描述"""
        # 从定位符推断元素类型
        element_type = "元素"
        for loc in locators:
            if 'btn' in loc['value'].lower() or 'button' in loc['value'].lower():
                element_type = "按钮"
                break
            elif 'edit' in loc['value'].lower() or 'input' in loc['value'].lower():
                element_type = "输入框"
                break
            elif 'text' in loc['type'].lower():
                element_type = "文本"
                break
        
        return f"{element_name}（{element_type}）"
    
    async def batch_generate(
        self,
        elements: list[dict]
    ) -> dict[int, str]:
        """
        批量生成描述（节省成本）
        
        Args:
            elements: 元素列表，每个元素包含 id, name, screen_name, locators
        
        Returns:
            元素ID到描述的映射
        """
        results = {}
        
        # 分批处理，避免超时
        batch_size = 5
        for i in range(0, len(elements), batch_size):
            batch = elements[i:i + batch_size]
            
            for element in batch:
                try:
                    description = await self.generate_description(
                        element_name=element['name'],
                        screen_name=element.get('screen_name', ''),
                        locators=element.get('locators', [])
                    )
                    results[element['id']] = description
                except Exception as e:
                    logger.error(f"Failed to generate for element {element['id']}: {e}")
                    results[element['id']] = element['name']
        
        return results


# 全局实例
element_description_service = ElementDescriptionService()
