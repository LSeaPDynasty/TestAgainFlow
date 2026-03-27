# TestFlow 执行引擎

TestFlow 的独立执行引擎应用程序，负责执行自动化测试任务。

## 架构

```
testflow/
├── frontend/     (端口 3002) - React UI
├── backend/      (端口 8000) - FastAPI 数据管理
└── executor/     (独立应用) - 执行引擎 ← 本组件
```

## 工作原理

执行引擎是一个**独立的应用程序**（非Web服务），通过以下方式工作：

1. **数据库轮询**: 定期检查后端数据库中的待执行任务
2. **任务执行**: 获取任务后执行测试步骤
3. **状态更新**: 将执行结果和日志写回数据库
4. **前端查询**: 前端通过后端API查询执行状态

### 数据流

```
前端 → 后端API → 数据库 (runs表) ← 执行引擎轮询
                              ↓
                        执行测试任务
                              ↓
                        数据库更新状态 ← 前端查询
```

## 快速开始

### Windows

双击运行 `start.bat`

或命令行：

```bash
cd executor
start.bat
```

### Linux/Mac

```bash
cd executor
chmod +x start.sh
./start.sh
```

## 手动启动

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行执行引擎
python main.py
```

## 配置

创建 `.env` 文件（可选）：

```env
# 日志级别
LOG_LEVEL=INFO

# ADB配置
ADB_PATH=adb
ADB_TIMEOUT=30
DEFAULT_DEVICE_TIMEOUT=120

# 执行配置
MAX_CONCURRENT_EXECUTIONS=5
EXECUTION_TIMEOUT=3600
STEP_TIMEOUT=60
SCREENSHOT_ON_FAILURE=true
SCREENSHOT_DIR=./screenshots

# 重试配置
MAX_RETRIES=3
RETRY_DELAY=1.0
```

## 功能特性

### 支持的执行类型

- **步骤执行**: 执行单个测试步骤
- **流程执行**: 执行多步骤流程
  - 标准流程: 步骤组合
  - DSL流程: 领域特定语言（待实现）
  - Python流程: Python脚本（待实现）
- **用例执行**: 执行完整用例（Setup + Main + Teardown）
- **套件执行**: 批量执行多个用例

### 支持的操作

#### 设备操作
- `click` - 点击元素
- `long_press` - 长按元素
- `input` - 输入文本
- `swipe` - 滑动（上下左右）
- `hardware_back` - 返回键

#### 等待操作
- `wait_element` - 等待元素出现
- `wait_time` - 等待指定时间

#### 断言操作
- `assert_text` - 断言文本内容
- `assert_exists` - 断言元素存在
- `assert_not_exists` - 断言元素不存在
- `assert_color` - 断言颜色（待实现）

#### 系统操作
- `start_activity` - 启动Activity
- `screenshot` - 截图

## 目录结构

```
executor/
├── app/
│   ├── core/              # 核心逻辑
│   │   ├── config.py      # 配置
│   │   ├── executor.py    # 主执行器
│   │   ├── task.py        # 任务模型
│   │   ├── execution_queue.py  # 执行队列
│   │   └── step_executor.py    # 步骤执行
│   ├── services/          # 服务
│   │   ├── adb_service.py # ADB通信
│   │   └── db_client.py   # 数据库客户端
│   └── __init__.py
├── main.py                # 应用入口
├── requirements.txt       # 依赖
├── start.bat             # Windows启动脚本
├── start.sh              # Linux/Mac启动脚本
└── README.md
```

## 运行界面

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        🤖 TestFlow Execution Engine v1.0.0                ║
║                                                           ║
║        Android 自动化测试执行引擎                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

🚀 初始化 TestFlow 执行引擎...
INFO:app.services.adb_service - 🔧 初始化 ADB 服务...
INFO:app.services.db_client - ✅ 连接数据库: .../testflow.db
INFO:app.core.executor - ✅ 执行引擎初始化完成
INFO:app.core.executor - ▶️  执行引擎开始运行...
INFO:app.core.executor - 📊 并发数: 5
INFO:app.core.executor - ⏱️  超时时间: 3600秒
INFO:app.core.executor - 💡 按 Ctrl+C 停止执行引擎
INFO:app.core.executor - 🔄 启动数据库轮询
INFO:app.core.executor - 🔄 启动工作线程
```

## 依赖

- Python 3.9+
- aiosqlite - 异步SQLite数据库访问
- pydantic - 数据验证
- pydantic-settings - 配置管理
- ADB (Android Debug Bridge) - 设备控制

## 日志

执行引擎运行时会生成日志文件：

- `executor.log` - 主日志文件
- 控制台输出 - 实时日志

日志级别可通过 `.env` 文件配置。

## 与后端交互

执行引擎通过以下方式与后端交互：

1. **读取任务**: 从 `runs` 表读取 `status='pending'` 的任务
2. **更新状态**: 执行过程中更新 `runs` 表的 `status` 字段
3. **保存日志**: 将执行日志写入 `runs` 表的 `logs` 字段
4. **保存结果**: 将执行结果写入 `result_summary` 字段

## 故障排查

### ADB 未找到

```
⚠️  ADB not found or not accessible
```

**解决方法**:
- 安装 Android SDK Platform Tools
- 确保 ADB 在系统 PATH 中
- 或在 `.env` 中配置 `ADB_PATH`

### 数据库连接失败

```
❌ unable to open database file
```

**解决方法**:
- 确保后端已初始化数据库
- 检查数据库路径是否正确
- 确保有数据库文件的读取权限

### 任务无法执行

```
❌ 任务失败: element not found
```

**解决方法**:
- 检查设备是否连接
- 确认元素定位器是否正确
- 查看详细日志了解失败原因

## 开发

### 添加新的操作类型

在 `app/core/step_executor.py` 中添加新的执行方法：

```python
async def _execute_your_action(self, step_data: Dict) -> TaskResult:
    """执行自定义操作"""
    # 实现逻辑
    return TaskResult.PASSED
```

### 自定义数据库查询

在 `app/services/db_client.py` 中添加新的查询方法。

## License

MIT
