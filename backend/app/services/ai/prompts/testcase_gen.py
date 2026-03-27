"""
Test case generation prompt templates
"""
from typing import Dict, List, Optional


def build_testcase_generation_prompt(
    json_data: Dict,
    elements: List[Dict],
    steps: List[Dict],
    flows: List[Dict],
    project_context: Optional[str] = None
) -> str:
    """
    Build prompt for test case generation from JSON

    Args:
        json_data: User-provided JSON describing the test case
        elements: Available elements in the project
        steps: Available steps in the project
        flows: Available flows in the project
        project_context: Optional project context
    """
    # Format elements
    elements_text = ""
    if elements:
        elements_text = "## Available Elements:\n"
        for el in elements[:50]:  # Limit to 50 elements
            # Format locators separately to avoid nested f-string
            locators_list = el.get('locators', [])[:3]
            locators_str = ', '.join([f"{l['type']}={l['value']}" for l in locators_list])

            elements_text += f"""
- {el['name']} (ID: {el['id']})
  Screen: {el.get('screen_name', 'N/A')}
  Description: {el.get('description', 'N/A')}
  Locators: {locators_str}
"""

    # Format steps
    steps_text = ""
    if steps:
        steps_text = "## Available Steps:\n"
        for step in steps[:30]:  # Limit to 30 steps
            steps_text += f"""
- {step['name']} (ID: {step['id']})
  Type: {step.get('step_type', 'N/A')}
  Description: {step.get('description', 'N/A')}
"""

    # Format flows
    flows_text = ""
    if flows:
        flows_text = "## Available Flows:\n"
        for flow in flows[:20]:  # Limit to 20 flows
            steps_count = flow.get('steps_count', 0)
            flows_text += f"""
- {flow['name']} (ID: {flow['id']})
  Description: {flow.get('description', 'N/A')}
  Steps: {steps_count} step(s)
"""

    prompt = f"""你是一位测试自动化架构专家。分析测试用例需求，并推荐使用现有资源或创建新资源的最佳方案。

## 测试用例需求:
```json
{json.dumps(json_data, indent=2, ensure_ascii=False)}
```

## 项目上下文:
{project_context or '无额外项目上下文'}

{elements_text}

{steps_text}

{flows_text}

## 你的分析任务:

1. **理解目标**: 这个测试用例要验证什么？

2. **资源搜索**: 识别哪些现有资源可以复用：
   - 流程: 可以复用整个流程吗？
   - 步骤: 哪些单独的步骤可以复用？
   - 元素: 需要哪些UI元素？

3. **差距分析**: 需要创建什么新资源？
   - 缺少的元素？
   - 缺少的步骤？
   - 缺少的流程？

4. **推荐方案**: 提供最佳方案：
   - 复用现有流程（如果80%+匹配）
   - 复用现有步骤并添加一些新步骤
   - 创建包含新资源的新测试用例

## 响应格式:

```json
{{
  "analysis": {{
    "goal": "<测试目标的简短中文描述>",
    "key_actions": ["<操作1>", "<操作2>", "..."]
  }},
  "resources_found": {{
    "flows": <匹配的流程数量>,
    "steps": <匹配的步骤数量>,
    "elements": <匹配的元素数量>
  }},
  "recommendations": [
    {{
      "type": "reuse_flow" | "reuse_step" | "create_flow" | "create_step" | "create_element",
      "flow_id": <复用流程时的ID>,
      "step_id": <复用步骤时的ID>,
      "element_id": <复用元素时的ID>,
      "name": "<新资源的建议名称>",
      "confidence": <0.0到1.0>,
      "reason": "<中文推荐理由>"
    }}
  ],
  "testcase_plan": {{
    "name": "<建议的中文测试用例名称>",
    "description": "<建议的中文描述>",
    "structure": {{
      "approach": "single_flow" | "mixed" | "inline_steps",
      "main_flow_id": <使用现有流程时的ID>,
      "flow_steps": [
        {{
          "step_id": <复用时的ID>,
          "step_name": "<新建时的名称>",
          "step_type": "<action, assertion等>",
          "element_id": <所需元素ID>,
          "element_name": "<要查找的元素名称>",
          "value": "<可选值>",
          "description": "<中文步骤描述>"
        }}
      ]
    }}
  }},
  "missing_resources": {{
    "elements": ["<元素名称1>", "<元素名称2>"],
    "steps": ["<步骤名称1>"]
  }}
}}
```

## 指导原则:

- **优先复用**: 如果现有流程覆盖80%以上的场景，推荐复用它
- **具体明确**: 建议新资源时提供具体的元素名称
- **模块化思维**: 将复杂场景分解为可复用的步骤
- **实用为先**: 推荐实践中最有效的方案，而不是理论上完美的

请彻底但简洁。专注于可操作的建议。所有描述性文本必须使用中文。
"""

    return prompt


def build_step_generation_prompt(
    step_description: str,
    elements: List[Dict],
    project_context: Optional[str] = None
) -> str:
    """Build prompt to generate a single step from description"""

    elements_text = ""
    if elements:
        elements_text = "## Available Elements:\n"
        for el in elements[:20]:
            elements_text += f"- {el['name']} (ID: {el['id']}): {el.get('description', 'N/A')}\n"

    prompt = f"""你是一位Android测试自动化专家。根据描述生成测试步骤配置。

## 步骤描述:
{step_description}

## 项目上下文:
{project_context or '无额外上下文'}

{elements_text}

## 步骤类型:
- `click`: 点击元素
- `send_keys`: 在字段中输入文本
- `swipe`: 执行滑动手势
- `wait`: 等待条件
- `assert_text`: 断言文本存在
- `assert_element`: 断言元素存在
- `assert_not_exists`: 断言元素不存在

## 响应格式:

```json
{{
  "name": "<snake_case格式的步骤名称>",
  "step_type": "<上述步骤类型之一>",
  "description": "<中文可读描述>",
  "element_id": <元素ID或null>,
  "element_name": "<要查找的元素名称>",
  "value": "<send_keys、断言的可选值>",
  "expected": "<可选的期望值>",
  "extra_params": {{<任何附加参数>}}
}}
```

生成一个实用的、可工作的步骤配置。所有描述必须使用中文。
"""

    return prompt
