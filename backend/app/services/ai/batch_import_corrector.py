"""
Batch Import Corrector - AI-powered JSON correction for batch import
"""
import json
import re
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.services.ai.config_service import AIConfigService
from app.services.ai.base import AIMessage


def extract_json_from_response(content: str) -> dict:
    """
    Extract JSON from AI response, handling markdown code blocks

    Args:
        content: Raw AI response content

    Returns:
        Parsed JSON dictionary
    """
    content = content.strip()

    # Check if content is wrapped in markdown code blocks
    if content.startswith("```"):
        # Try to extract JSON from ```json ... ``` blocks
        match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            content = match.group(1)
        else:
            # Fallback: remove all backticks and language markers
            content = content.strip('`').strip()
            if content.lower().startswith('json'):
                content = content[4:].strip()

    return json.loads(content)


class BatchImportCorrector:
    """批量导入JSON修正服务"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_config_service = AIConfigService(db)

    async def correct_and_validate(
        self,
        json_data: any,
        project_id: Optional[int] = None
    ) -> Dict:
        """
        修正并验证批量导入的JSON数据

        Args:
            json_data: 原始JSON数据（可以是单个对象或数组）
            project_id: 项目ID

        Returns:
            修正后的数据和建议
        """
        # 标准化为数组格式
        if isinstance(json_data, dict):
            testcases = [json_data]
        elif isinstance(json_data, list):
            testcases = json_data
        else:
            raise ValueError("JSON数据格式错误：必须是对象或数组")

        # 使用AI分析和修正
        prompt = self._build_correction_prompt(testcases, project_id)

        try:
            provider = self.ai_config_service.get_provider()
            messages = [AIMessage(role="user", content=prompt)]
            response, stats = await provider.chat_completion(
                messages=messages,
                temperature=0.3
            )

            # 解析AI响应
            result = extract_json_from_response(response.content)

            # 合并修正结果
            return {
                "testcases": result.get("testcases", testcases),
                "corrections": result.get("corrections", []),
                "warnings": result.get("warnings", []),
                "needs_review": result.get("needs_review", 0)
            }

        except Exception as e:
            # 如果AI修正失败，返回基本验证结果
            return self._basic_validation(testcases)

    def _build_correction_prompt(self, testcases: List[Dict], project_id: Optional[int]) -> str:
        """构建AI修正prompt"""

        testcases_json = json.dumps(testcases, ensure_ascii=False, indent=2)

        prompt = f"""你是一位测试自动化专家。请分析和修正以下批量导入的测试用例JSON数据。

## 原始数据:
```json
{testcases_json}
```

## 你的任务:

**重要**: 这是一个复杂的测试用例数据结构，包含flow、steps、assert等嵌套字段。你必须完整保留所有这些数据，只做最小限度的修正。

1. **绝对保留原始数据结构**:
   - case_name: 测试用例名称（保持不变）
   - flow: 包含name和step数组（完整保留）
   - aseert: 断言数组（完整保留，注意原文拼写是aseert）
   - teardown: 清理步骤（完整保留）
   - setup: 前置步骤（完整保留）
   - source: 来源信息（完整保留）
   - 所有嵌套结构都要保持不变

2. **只修正以下字段**:
   - priority: 如果不是P0/P1/P2/P3格式，修正为P1
   - 其他字段一律保持原样

3. **返回格式**:
   必须返回与输入完全相同的JSON结构，只修正priority字段

## 输出示例:

如果输入是:
```json
{{
  "case_name": "测试",
  "priority": "high",
  "flow": {{
    "name": "MyFlow",
    "step": [...]
  }}
}}
```

输出应该是:
```json
{{
  "case_name": "测试",
  "priority": "P1",
  "flow": {{
    "name": "MyFlow",
    "step": [...]
  }}
}}
```

## 响应格式:

```json
{{
  "testcases": [完整的原始测试用例数组，只修正priority],
  "corrections": [
    {{
      "field": "priority",
      "issue": "格式错误",
      "old_value": "high",
      "new_value": "P1"
    }}
  ],
  "warnings": [],
  "needs_review": 0
}}
```

**再次强调**: 必须完整保留原始JSON的所有字段和结构，不要简化、删除或重组任何内容。
"""
        return prompt

    def _basic_validation(self, testcases: List[Dict]) -> Dict:
        """基本验证（AI修正失败时的fallback）- 保留原始数据结构"""

        validated = []
        corrections = []
        warnings = []

        for idx, tc in enumerate(testcases):
            # 创建副本，不修改原始数据
            tc_validated = tc.copy()

            # 标准化优先级
            if "priority" in tc_validated:
                valid_priorities = ["P0", "P1", "P2", "P3"]
                priority = tc_validated["priority"]
                if isinstance(priority, str) and priority.upper() in valid_priorities:
                    tc_validated["priority"] = priority.upper()
                else:
                    corrections.append({
                        "field": "priority",
                        "issue": "优先级格式错误",
                        "old_value": priority,
                        "new_value": "P1"
                    })
                    tc_validated["priority"] = "P1"
            else:
                tc_validated["priority"] = "P1"

            # 保留所有原始字段，不做简化
            validated.append(tc_validated)

        return {
            "testcases": validated,
            "corrections": corrections,
            "warnings": warnings,
            "needs_review": 0
        }
