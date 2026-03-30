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
        import re

        # 从元素名称推断功能
        name_lower = element_name.lower()

        # 推断元素类型
        element_type = "元素"
        if any(kw in name_lower for kw in ['btn', 'button', 'click', 'submit']):
            element_type = "按钮"
        elif any(kw in name_lower for kw in ['input', 'edit', 'field', 'text']):
            element_type = "输入框"
        elif any(kw in name_lower for kw in ['text', 'label', 'title', 'msg']):
            element_type = "文本"
        elif any(kw in name_lower for kw in ['image', 'img', 'icon', 'avatar']):
            element_type = "图片"
        elif any(kw in name_lower for kw in ['switch', 'toggle', 'check']):
            element_type = "开关"
        elif any(kw in name_lower for kw in ['list', 'recycler', 'grid']):
            element_type = "列表"

        # 从定位符推断
        locator_type = ""
        for loc in locators:
            val = loc['value'].lower()
            if 'id' in loc['type'].lower():
                if 'btn' in val or 'button' in val:
                    locator_type = "按钮"
                elif 'input' in val or 'edit' in val or 'text' in val:
                    locator_type = "输入框"
                elif 'config' in val or 'setting' in val:
                    locator_type = "配置"

        # 从元素名称推断功能
        function_desc = ""
        if 'config' in name_lower or 'setting' in name_lower:
            function_desc = "配置"
        elif 'login' in name_lower:
            function_desc = "登录"
        elif 'submit' in name_lower or 'confirm' in name_lower:
            function_desc = "提交确认"
        elif 'cancel' in name_lower or 'close' in name_lower:
            function_desc = "取消"
        elif 'delete' in name_lower or 'remove' in name_lower:
            function_desc = "删除"
        elif 'save' in name_lower:
            function_desc = "保存"
        elif 'rtk' in name_lower:
            function_desc = "RTK"
        else:
            # 驼峰命名转可读格式
            parts = re.findall('[A-Z][a-z]*|[a-z]+', element_name)
            if parts:
                function_desc = parts[0]

        # 组合描述
        if function_desc and locator_type:
            return f"{function_desc}{locator_type}"
        elif function_desc:
            return f"{function_desc}{element_type}"
        elif locator_type:
            return f"{locator_type}"
        else:
            # 尝试美化元素名称
            if element_name == element_name.lower():
                return f"{element_name}（{element_type}）"
            # 驼峰转可读格式
            readable = ' '.join(re.findall('[A-Z][a-z]*|[a-z]+', element_name))
            return f"{readable}（{element_type}）"
    
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
