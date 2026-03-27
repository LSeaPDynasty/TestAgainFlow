# 执行器能力注册系统使用指南

## 📖 概述

执行器能力注册系统是一个灵活的架构，解决了添加新操作类型需要修改前端、后端、执行器三个地方的问题。

**核心思想：**
- 执行器启动时自动向后端注册自己支持的操作类型
- 后端累积所有见过的操作类型（只增不减）
- 前端从API动态获取操作类型定义
- 执行前校验用例是否可以在执行器上运行

## 🎯 解决的问题

### 之前的问题
```
添加新操作（比如"screenshot"）需要修改：
1. 前端 Steps/index.tsx - 硬编码操作类型列表 ❌
2. 后端 Schema - 可能需要更新 ❌
3. 执行器 step_executor.py - 硬编码if-elif分支 ❌
4. 重启所有服务 ❌
```

### 现在的方案
```
添加新操作只需：
1. 在执行器中实现 _execute_xxx 方法 ✅
2. 在 capability_registration.py 的 builtin_actions 中添加定义 ✅
3. 重启执行器（自动注册到后端）✅
4. 前端自动发现新操作（无需修改）✅
```

## 🚀 快速开始

### 1. 运行数据库迁移

```bash
cd C:\Users\lsea.yu\Desktop\docs\testflow\backend
alembic upgrade head
```

这将创建以下表：
- `executors` - 执行器实例表
- `action_types` - 操作类型表（累积，只增不减）
- `executor_action_capabilities` - 执行器-操作类型关联表

### 2. 启动后端

```bash
cd C:\Users\lsea.yu\Desktop\docs\testflow\backend
python run.py
```

后端将提供以下新API：
- `POST /api/v1/executor-capabilities/register` - 执行器注册
- `POST /api/v1/executor-capabilities/heartbeat` - 执行器心跳
- `GET /api/v1/executor-capabilities/action-types` - 获取操作类型列表
- `POST /api/v1/executor-capabilities/check-capability` - 检查操作能力
- `POST /api/v1/executor-capabilities/validate-testcase` - 验证用例

### 3. 启动执行器

```bash
cd C:\Users\lsea.yu\Desktop\docs\testflow\executor
python main.py
```

执行器启动时会自动：
1. 向后端注册自己的能力
2. 启动心跳任务（每30秒）
3. 发送支持的操作类型列表

### 4. 启动前端

```bash
cd C:\Users\lsea.yu\Desktop\docs\testflow\frontend
npm run dev
```

前端会自动从后端获取操作类型列表，无需修改代码。

## 📝 如何添加新操作类型

### 方法1：添加内置操作

**1. 在执行器中实现操作逻辑**

编辑 `executor/app/core/step_executor.py`：

```python
async def _execute_my_new_action(self, step_data: Dict) -> TaskResult:
    """执行我的新操作"""
    self.task.log(f"   🔧 执行新操作")

    # 实现你的逻辑
    success = await self.driver.do_something(...)

    if success:
        self.task.log(f"   ✅ 操作成功")
        return TaskResult.PASSED
    else:
        self.task.log(f"   ❌ 操作失败")
        return TaskResult.FAILED
```

**2. 在execute_with_data中注册**

编辑 `executor/app/core/step_executor.py` 的 `execute_with_data` 方法：

```python
elif action_type == 'my_new_action':
    result = await self._execute_my_new_action(step_data)
```

**3. 添加操作类型定义**

编辑 `executor/app/services/capability_registration.py` 的 `builtin_actions`：

```python
'my_new_action': {
    'display_name': '我的新操作',
    'category': '自定义',
    'description': '这是一个自定义操作',
    'color': 'purple',
    'requires_element': False,
    'requires_value': True,
},
```

**4. 重启执行器**

```bash
# 停止执行器
# Ctrl+C

# 重新启动
python main.py
```

执行器启动时会自动注册新操作到后端，前端会自动发现。

### 方法2：添加插件操作（未来功能）

创建 `executor/app/actions/my_plugin_action.py`：

```python
from ..actions.base_action import BaseAction

class MyPluginAction(BaseAction):
    type_code = 'my_plugin_action'
    category = '插件'
    display_name = '我的插件操作'

    async def execute(self, step_data, driver):
        # 实现逻辑
        pass
```

执行器会自动发现并加载插件操作。

## 🔧 执行前校验

### 校验单个用例

```typescript
import { validateTestcase } from '@/services/actionTypes';

const result = await validateTestcase({
  testcase_id: 123,
  executor_id: 'executor-pixel5-001',
  skip_unsupported: false,
});

if (result.can_execute) {
  console.log('用例可以执行');
} else {
  console.warn('不支持的操作:', result.unsupported_actions);
  console.log('建议:', result.recommendation);
}
```

### 批量校验（在Runs页面）

在运行测试前，检查所有用例：

```typescript
const unsupportedTestcases = [];

for (const testcase of selectedTestcases) {
  const validation = await validateTestcase({
    testcase_id: testcase.id,
    skip_unsupported: true, // 跳过不支持的用例
  });

  if (!validation.can_execute) {
    unsupportedTestcases.push({
      testcase,
      validation,
    });
  }
}

if (unsupportedTestcases.length > 0) {
  Modal.warning({
    title: '部分用例无法执行',
    content: (
      <div>
        <p>以下用例包含不支持的操作：</p>
        {unsupportedTestcases.map(({ testcase, validation }) => (
          <div key={testcase.id}>
            <strong>{testcase.name}</strong>
            <ul>
              {validation.unsupported_actions.map(action => (
                <li key={action.action_type}>
                  {action.action_type} ({action.step_count} 个步骤)
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    ),
  });
}
```

## 📊 数据库Schema

### executors 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| executor_id | VARCHAR(100) | 执行器唯一标识 |
| executor_version | VARCHAR(20) | 执行器版本 |
| hostname | VARCHAR(100) | 主机名 |
| ip_address | VARCHAR(50) | IP地址 |
| last_seen | DATETIME | 最后心跳时间 |
| is_online | BOOLEAN | 是否在线 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### action_types 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| type_code | VARCHAR(50) | 操作类型代码（唯一） |
| display_name | VARCHAR(100) | 显示名称 |
| category | VARCHAR(50) | 分类 |
| description | VARCHAR(500) | 描述 |
| color | VARCHAR(20) | 前端显示颜色 |
| requires_element | BOOLEAN | 是否需要元素 |
| requires_value | BOOLEAN | 是否需要参数值 |
| config_schema | TEXT | 配置Schema（JSON） |
| first_seen_executor_id | VARCHAR(100) | 首次注册的执行器ID |
| first_seen_at | DATETIME | 首次发现时间 |
| is_deprecated | BOOLEAN | 是否已废弃 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### executor_action_capabilities 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| executor_id | VARCHAR(100) | 执行器ID |
| action_type_code | VARCHAR(50) | 操作类型代码 |
| executor_version | VARCHAR(20) | 注册时的执行器版本 |
| registered_at | DATETIME | 注册时间 |
| implementation_version | VARCHAR(20) | 实现版本 |

## 🔍 故障排除

### 问题1：前端没有显示新操作

**可能原因：**
1. 执行器没有成功注册
2. 前端缓存未刷新

**解决方案：**
1. 查看执行器日志，确认注册成功
2. 前端刷新页面或清除缓存
3. 检查后端API是否返回新操作

### 问题2：执行器注册失败

**可能原因：**
1. 后端未启动
2. 网络连接问题
3. 数据库未迁移

**解决方案：**
1. 确认后端运行正常：`curl http://localhost:8000/health`
2. 检查执行器配置文件中的 `backend_url`
3. 运行数据库迁移：`alembic upgrade head`

### 问题3：用例校验失败

**可能原因：**
1. 执行器不在线
2. 操作类型未注册

**解决方案：**
1. 检查执行器是否在线：`GET /api/v1/executor/status`
2. 查看执行器支持的操作类型：`GET /api/v1/executor-capabilities/action-types`

## 📈 监控和统计

### 查看所有执行器

```bash
curl http://localhost:8000/api/v1/executor/status
```

### 查看所有操作类型

```bash
curl http://localhost:8000/api/v1/executor-capabilities/action-types
```

### 统计信息

- 总操作类型数量
- 每个分类的操作数量
- 每个执行器支持的操作数量

## 🎉 总结

使用新的执行器能力注册系统后：

✅ **添加新操作只需3步：**
1. 在执行器中实现逻辑
2. 添加操作类型定义
3. 重启执行器

✅ **前端自动发现：**
- 无需修改前端代码
- 操作类型自动分类
- 颜色和配置自动应用

✅ **执行前校验：**
- 提前发现不兼容的操作
- 避免执行失败
- 提供明确的警告和建议

✅ **向后兼容：**
- 如果API不可用，使用fallback硬编码数据
- 平滑迁移路径
