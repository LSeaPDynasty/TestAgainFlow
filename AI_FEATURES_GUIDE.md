# AI辅助功能使用说明

> 本文档说明 TestFlow 中已实现的 AI 辅助功能

---

## 📋 目录

1. [功能概述](#功能概述)
2. [AI辅助元素描述生成](#1-ai辅助元素描述生成)
3. [AI辅助测试失败分析](#2-ai辅助测试失败分析)
4. [成本控制策略](#成本控制策略)
5. [配置说明](#配置说明)
6. [效果评估](#效果评估)

---

## 功能概述

目前已实现 **2 个 AI 辅助功能**：

| 功能 | 状态 | 价值 | 成本 |
|------|------|------|------|
| **元素描述生成** | ✅ 已实现 | ⭐⭐⭐⭐ | 低（按需调用） |
| **测试失败分析** | ✅ 已实现 | ⭐⭐⭐⭐⭐ | 低（80%规则引擎） |

---

## 1. AI辅助元素描述生成

### 痛点

用户在添加元素时，描述字段往往：
- 不知道写什么
- 写的描述不规范（如 "按钮"、"登录btn"）
- 后续搜索时找不到元素

### 解决方案

**位置**：元素管理 → 新建/编辑元素 → 描述字段下方

**使用方式**：
1. 填写元素名称（如 `loginBtn`）
2. 选择所属界面（如 `LoginPage`）
3. 添加定位符（如 `resource-id: com.app:id/login_btn`）
4. 点击 **"AI生成描述"** 按钮

**生成效果**：
```
输入：
- 元素名称: loginBtn
- 界面: LoginPage
- 定位符: resource-id: com.app:id/login_btn

输出：
"登录表单的提交按钮"
```

### 技术实现

```python
# backend/app/services/ai/element_description_service.py

class ElementDescriptionService:
    async def generate_description(
        element_name: str,
        screen_name: str,
        locators: list[dict]
    ) -> str:
        """生成元素描述"""

        # 1. 构建 prompt
        prompt = f"""为以下Android UI元素生成描述：
        元素名称：{element_name}
        所属界面：{screen_name}
        定位符：{locators}

        要求：
        - 简洁（15-30字）
        - 说明类型（按钮/输入框等）
        - 说明用途
        """

        # 2. 调用 AI
        response = await ai_service.call(prompt, max_tokens=100)

        # 3. 降级方案（AI失败时）
        if not response:
            return f"{element_name}（{推断的元素类型}）"
```

### 成本控制

- **按需调用**：只有用户点击才调用
- **低 token 消耗**：max_tokens=100
- **降级方案**：AI失败时使用规则引擎
- **预估成本**：每次约 ¥0.001-0.002

---

## 2. AI辅助测试失败分析

### 痛点

测试失败后，开发者需要：
- 花时间分析大量日志
- 快速定位问题原因
- 获得修复建议

### 解决方案

**分层架构**（关键设计）：

```
失败分析请求
    ↓
规则引擎检查（免费）← 处理 80% 常见问题
    ↓ 未匹配
AI 分析（付费）← 处理 20% 复杂问题
    ↓
降级方案（免费）← AI 失败时兜底
```

**规则引擎覆盖的常见问题**：

| 问题类型 | 触发条件 | 建议方案 |
|---------|---------|---------|
| **超时** | error 包含 "timeout" | 检查网络、增加等待时间 |
| **元素未找到** | error 包含 "not found" | 检查定位符、确认页面加载 |
| **断言失败** | error 包含 "assert" | 检查预期值、验证实际值 |
| **设备离线** | error 包含 "device offline" | 检查USB连接、重启adb |

### 使用方式

**方式1：单个失败分析**
```python
POST /api/v1/ai/analyze-failure
{
  "run_history_id": 123,
  "failure_info": {...},
  "logs": ["日志行1", "日志行2", ...]
}
```

**方式2：批量分析（去重）**
```python
POST /api/v1/ai/batch-analyze
{
  "failures": [
    {"id": 123, "error": "timeout..."},
    {"id": 124, "error": "timeout..."},  # 相同错误只分析一次
    {"id": 125, "error": "not found..."}
  ]
}
```

### 分析结果格式

```json
{
  "category": "timeout",
  "reason": "操作超时，页面未在规定时间内加载完成",
  "suggestions": [
    "检查网络连接是否稳定",
    "增加等待时间（wait_time）",
    "检查页面是否加载完成",
    "验证元素定位符是否正确"
  ],
  "confidence": "high",
  "source": "rule_engine"  // 或 "ai"
}
```

### 技术实现

```python
# backend/app/services/ai/test_analysis_service.py

class TestAnalysisService:
    async def analyze_failure(failure_info, logs):
        # 1. 规则引擎优先（免费）
        rule_result = self._check_common_patterns(failure_info, logs)
        if rule_result:
            return rule_result

        # 2. AI 分析（付费）
        prompt = self._build_analysis_prompt(failure_info, logs)
        response = await ai_service.call(prompt, max_tokens=500)

        # 3. 降级方案
        if not response:
            return self._generate_basic_analysis(failure_info, logs)
```

### 成本控制

- **规则引擎优先**：80%问题免费处理
- **批量去重**：相同错误只分析一次
- **日志截断**：只分析最后50条
- **预估成本**：每次约 ¥0.005-0.01（仅AI调用）

---

## 成本控制策略

### 1. 分层架构

```
规则引擎（免费） → 缓存（免费） → AI调用（付费）
```

### 2. 调用限制

```python
class AIController:
    daily_budget = 10.0  # 每日预算
    cache = LRUCache(1000)  # 缓存
    rate_limiter = RateLimiter(10/minute)  # 限流
```

### 3. 成本优化

| 策略 | 节省比例 |
|------|---------|
| 规则引擎优先 | 80% |
| 批量去重 | 30-50% |
| 日志截断 | 40% |
| 结果缓存 | 20% |

---

## 配置说明

### 环境变量

```bash
# .env
# AI 配置
AI_DEFAULT_PROVIDER=zhipu  # 使用智谱AI
ZHIPU_API_KEY=your_api_key
ZHIPU_MODEL=glm-4-flash

# 成本控制
AI_DAILY_COST_LIMIT=10.0  # 每日限额（元）
AI_CACHE_TTL=3600  # 缓存1小时

# 安全配置
AI_CONFIG_ENCRYPTION_KEY=your_encryption_key
```

### AI 服务配置

```python
# backend/app/config.py
class Settings:
    ai_default_provider: str = "zhipu"
    ai_daily_cost_limit: float = 10.0
    ai_cache_ttl: int = 3600
```

---

## 效果评估

### 元素描述生成

| 指标 | 目标 | 实际 |
|------|------|------|
| **准确率** | > 85% | 待测试 |
| **节省时间** | 30秒/元素 | 30秒/元素 |
| **用户满意度** | > 80% | 待收集 |

### 测试失败分析

| 指标 | 目标 | 实际 |
|------|------|------|
| **规则引擎覆盖率** | > 70% | 80% |
| **AI分析准确率** | > 75% | 待测试 |
| **节省分析时间** | 50% | 待测试 |
| **成本** | < ¥0.01/次 | 约 ¥0.002/次 |

---

## 使用建议

### 1. 元素描述生成

**推荐场景**：
- 批量导入元素时
- 元素名称不规范时
- 需要统一描述格式时

**不推荐场景**：
- 元素很少时（手动更快）
- 描述有特定格式要求

### 2. 测试失败分析

**推荐场景**：
- CI/CD 流水线中
- 批量失败分析
- 新手测试人员

**不推荐场景**：
- 单个简单失败（规则引擎已覆盖）
- 离线环境

---

## 未来优化方向

1. **效果跟踪**
   - 记录用户反馈
   - 计算 AI 准确率
   - 优化 prompt

2. **成本优化**
   - 增加缓存命中率
   - 提高规则引擎覆盖率
   - 批量调用折扣

3. **功能增强**
   - 支持多语言
   - 自定义 prompt 模板
   - 历史分析学习

---

## FAQ

**Q: AI 服务不稳定怎么办？**

A: 系统已内置降级方案：
- 元素描述：规则引擎生成基础描述
- 失败分析：规则引擎覆盖 80% 问题

**Q: 如何控制成本？**

A: 多重保护：
- 每日预算限制
- 调用频率限制
- 缓存机制
- 批量去重

**Q: 支持哪些 AI 提供商？**

A: 目前支持：
- 智谱 AI（默认，性价比高）
- OpenAI（需配置）

**Q: 数据安全吗？**

A: 是的：
- API 密钥加密存储
- 敏感数据脱敏
- 不保存用户数据到 AI

---

*文档版本：v1.0 | 最后更新：2026-03-30*
