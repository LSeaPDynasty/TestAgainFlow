"""
Element matching prompt templates
"""
from typing import Dict, List, Optional


def build_element_match_prompt(
    dom_element: Dict,
    candidates: List[Dict],
    screen_context: Optional[str] = None
) -> str:
    """
    Build prompt for element matching

    Args:
        dom_element: The DOM element from viewer
        candidates: List of existing elements to match against
        screen_context: Optional screen/context information
    """
    # Format candidates for display
    candidates_text = ""
    for i, candidate in enumerate(candidates, 1):
        candidates_text += f"""
Candidate {i}:
  - ID: {candidate.get('id')}
  - Name: {candidate.get('name')}
  - Description: {candidate.get('description', 'N/A')}
  - Locators:
"""
        for locator in candidate.get('locators', []):
            candidates_text += f"    * {locator.get('type')}: {locator.get('value')}\n"

    prompt = f"""你是一位Android UI自动化测试专家。你的任务是判断数据库中是否有与DOM查看器中的新元素匹配的现有元素。

## 新DOM元素（来自查看器）：
```
文本: {dom_element.get('text', 'N/A')}
资源ID: {dom_element.get('resource-id', 'N/A')}
类名: {dom_element.get('class', 'N/A')}
内容描述: {dom_element.get('content-desc', 'N/A')}
XPath: {dom_element.get('xpath', 'N/A')}
边界: {dom_element.get('bounds', 'N/A')}
```

## 界面上下文:
{screen_context or '无额外上下文信息'}

## 现有元素候选项:
{candidates_text}

## 匹配标准:

1. **精确匹配** (分数: 1.0):
   - 资源ID完全匹配
   - 或 文本 + 类名完全匹配且界面上下文相同

2. **模糊匹配** (分数: 0.7-0.9):
   - 文本相似（拼写错误、细微差异）
   - 资源ID相似（包含相同关键词）
   - 定位符指向相似的元素

3. **语义匹配** (分数: 0.6-0.8):
   - 元素具有相同用途（例如，都是登录按钮）
   - 基于文本/描述具有相似功能
   - 可用于相同的测试场景

## 你的任务:

分析新DOM元素与每个候选项的匹配情况，并提供：

1. **最佳匹配**: 哪个候选项（如果有）是最佳匹配？
2. **匹配类型**: strict（精确）、fuzzy（模糊）或 semantic（语义）
3. **相似度分数**: 0.0到1.0之间的浮点数
4. **置信度**: 你对这次匹配的信心（high/medium/low）
5. **推理说明**: 决策的详细解释（**必须使用中文**）
6. **建议**: "reuse"（复用现有元素）或 "create_new"（创建新元素）
7. **推荐名称**: 如果创建新元素，建议的元素名称（使用snake_case格式，如 login_button）

## 响应格式:

请以JSON格式提供响应：
```json
{{
  "best_match_id": <候选项ID或null>,
  "match_type": <"strict" | "fuzzy" | "semantic" | "none">,
  "similarity_score": <0.0到1.0>,
  "confidence": <"high" | "medium" | "low">,
  "reasoning": "<详细的中文解释>",
  "recommendation": <"reuse" | "create_new">,
  "suggested_name": "<如果创建新元素，建议的元素名称>",
  "suggested_locators": [
    {{"type": "<定位符类型>", "value": "<定位符值>", "priority": <1-5>}}
  ]
}}
```

如果不存在良好匹配，将best_match_id设置为null并建议"create_new"。

请彻底分析但要简洁。专注于测试自动化的实用性。所有文本说明必须使用中文。
"""

    return prompt


def build_element_name_suggestion_prompt(dom_element: Dict, screen_context: Optional[str] = None) -> str:
    """Build prompt to suggest element name and locators"""

    prompt = f"""你是一位Android UI自动化测试专家。请为这个DOM元素建议一个合适的名称和定位符。

## DOM元素:
```
文本: {dom_element.get('text', 'N/A')}
资源ID: {dom_element.get('resource-id', 'N/A')}
类名: {dom_element.get('class', 'N/A')}
内容描述: {dom_element.get('content-desc', 'N/A')}
```

## 界面上下文:
{screen_context or '无额外上下文信息'}

## 你的任务:

1. 建议一个清晰、描述性的元素名称，遵循以下规范：
   - 使用snake_case格式
   - 包含元素类型（button、text_field等）
   - 具体但简洁
   - 示例：login_button、username_input、settings_menu_item

2. 按优先级顺序建议定位符（1=最高优先级）：
   - resource-id（如果唯一且稳定）
   - text（如果唯一且稳定）
   - content-desc（如果可用）
   - xpath（作为备选）
   - class（仅在与其它属性结合时使用）

## 响应格式:

```json
{{
  "suggested_name": "<元素名称>",
  "suggested_locators": [
    {{"type": "resource-id", "value": "<值>", "priority": 1}},
    {{"type": "text", "value": "<值>", "priority": 2}}
  ],
  "reasoning": "<中文简短说明>"
}}
```

请用中文提供推理说明。
"""

    return prompt
