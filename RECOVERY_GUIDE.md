# 测试执行恢复策略指南

## 问题场景
当一个套件中的某个用例失败后，APP 可能停留在某个中间页面，导致下一个用例无法正常执行。

## 解决方案

### 方案 1：在每个用例中添加 Teardown Flow（推荐）✅

#### 步骤 1：创建"回到首页"Flow

在 **流程管理** 页面创建新流程：

```
流程名称：回到首页 (Reset to Home)
流程描述：失败后回到首页，确保下个用例从干净状态开始
```

**步骤配置：**

| 步骤名称 | 操作类型 | 元素/参数 | 说明 |
|---------|---------|----------|------|
| 按 HOME 键 | hardware_back | - | 按 Home 键回到桌面（可选） |
| 启动应用 | start_activity | activity: com.your.app/.MainActivity | 启动应用主 Activity |
| 等待首页加载 | wait_element | element_id: xxx | 等待首页元素出现 |
| 等待稳定 | wait_time | duration: 1000 | 等待 1 秒让页面稳定 |

#### 步骤 2：将 Flow 添加到用例

1. 进入 **用例管理** 页面
2. 编辑用例
3. 切换到 **Teardown** 标签页
4. 选择 **"回到首页"** Flow
5. 设置执行顺序
6. 保存用例

**优点：**
- ✅ 每个用例可以有不同的恢复策略
- ✅ Teardown 总是执行，即使用例失败
- ✅ 灵活性高

---

### 方案 2：在数据库中配置全局恢复 Flow

#### 步骤 1：创建全局恢复 Flow

同上，创建一个 **"全局恢复"** Flow。

#### 步骤 2：更新 Suite 模型

需要修改数据库，为 `suites` 表添加 `recovery_flow_id` 字段：

```sql
ALTER TABLE suites ADD COLUMN recovery_flow_id INTEGER;
```

#### 步骤 3：在套件中指定恢复 Flow

更新套件配置，指定 `recovery_flow_id`。

---

### 方案 3：在配置文件中设置默认恢复策略

创建配置文件 `config/recovery.py`：

```python
# 默认恢复步骤配置
DEFAULT_RECOVERY_STEPS = [
    {
        "action_type": "hardware_back",
        "description": "按返回键"
    },
    {
        "action_type": "start_activity",
        "action_value": "com.your.app/.MainActivity",
        "description": "启动应用"
    },
    {
        "action_type": "wait_time",
        "action_value": "1000",
        "description": "等待稳定"
    }
]
```

---

## 最佳实践建议

### 1. 创建通用的"回到首页"Flow

**建议配置：**

```yaml
流程名称: 回到首页 (Reset to Home)
步骤:
  - 操作: 按 HOME 键
    类型: hardware_back
    说明: 回到桌面（可选）

  - 操作: 启动应用
    类型: start_activity
    参数:
      activity: com.example.app/.MainActivity
    说明: 启动主Activity

  - 操作: 等待首页
    类型: wait_element
    参数:
      element_id: 123  # 首页标志性元素
      timeout: 5000
    说明: 等待首页元素出现

  - 操作: 等待稳定
    类型: wait_time
    参数:
      duration: 1000
    说明: 等待1秒让页面完全加载
```

### 2. 为不同类型的测试创建不同的恢复策略

| 测试类型 | 恢复策略 |
|---------|---------|
| 登录测试 | 退出登录 → 回到首页 |
| 支付测试 | 取消支付 → 回到首页 |
| 设置测试 | 恢复默认设置 → 回到首页 |
| 多页面测试 | 直接回到首页 |

### 3. 执行顺序建议

**每个用例的执行顺序：**
```
Setup (可选)
    ↓
Main (测试步骤)
    ↓
Teardown (总是执行) ← 包含"回到首页"
```

**套件执行顺序：**
```
用例 1
    ↓
用例 1 的 Teardown (回到首页)
    ↓
用例 2 (从首页开始)
    ↓
用例 2 的 Teardown (回到首页)
    ↓
用例 3 (从首页开始)
    ↓
...
```

---

## 验证方法

### 1. 测试用例失败后是否回到首页

**步骤：**
1. 创建一个故意失败的用例
   - Main: 点击不存在的元素
   - Teardown: "回到首页" Flow

2. 将用例添加到套件并执行

3. 检查日志：
   ```
   ❌ Main失败: 点击xxx
   🧹 Teardown阶段 (1 个流程)
   ✅ 回到首页执行成功
   ```

4. 手动检查设备是否回到首页

### 2. 测试套件连续执行

**步骤：**
1. 创建 3 个测试用例，每个都有 teardown
2. 添加到套件中
3. 执行套件
4. 观察每个用例执行后是否都回到首页

---

## 常见问题

### Q1: Teardown 执行失败怎么办？
**A:** Teardown 失败不影响用例结果，但会记录警告日志。建议：
- 确保 Teardown Flow 中的步骤足够健壮
- 使用合理的超时时间
- 添加重试机制

### Q2: 如果应用崩溃了怎么办？
**A:** 可以在 Teardown 中添加：
```yaml
- 操作: 启动应用
  类型: start_activity
  说明: 如果应用崩溃，重新启动
```

### Q3: 有些用例需要特殊恢复策略怎么办？
**A:** 为每个用例配置不同的 Teardown Flow：
- 登录用例 → Teardown: 退出登录
- 支付用例 → Teardown: 取消支付
- 普通用例 → Teardown: 回到首页

---

## 代码更新说明

**已修复的问题：**
- ✅ Teardown 现在总是执行，即使 Main 失败
- ✅ Teardown 失败不会导致用例结果改变
- ✅ 添加了详细的日志记录

**修改的文件：**
- `executor/app/core/executor.py` - `_execute_testcase` 方法

**修改内容：**
- 使用 `final_result` 变量跟踪用例结果
- Main 失败后使用 `break` 而不是 `return`
- 无论 Main 成功与否，都执行 Teardown
- Teardown 失败记录为 WARNING 而不是 ERROR
