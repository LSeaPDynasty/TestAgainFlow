# TestFlow - Android自动化测试平台

Android自动化测试平台 - 支持UI自动化测试、流程编排、执行管理

## 架构

TestFlow采用三层架构，由前端、后端和执行引擎组成：

```
testflow/
├── frontend/     (端口 3002) - React前端界面
├── backend/      (端口 8000) - FastAPI后端服务
└── executor/     (独立应用) - 执行引擎应用程序
```

### 组件说明

#### 1. Frontend (前端)
- **端口**: 3002
- **技术栈**: React + TypeScript + Vite + Ant Design
- **功能**: 用户界面、测试管理、结果展示

#### 2. Backend (后端)
- **端口**: 8000
- **技术栈**: FastAPI + SQLAlchemy + SQLite
- **功能**: 数据管理、API服务、业务逻辑

#### 3. Executor (执行引擎)
- **类型**: 独立应用程序（非Web服务）
- **技术栈**: Python + ADB + SQLite
- **功能**: 测试执行、设备控制、任务调度
- **工作方式**: 轮询数据库获取任务并执行

## 快速开始

### 前置要求

- Python 3.9+
- Node.js 18+
- ADB (Android Debug Bridge)

### 安装

```bash
# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装执行引擎依赖
cd ../executor
pip install -r requirements.txt

# 安装前端依赖
cd ../frontend
npm install
```

### 启动服务

#### Windows
```bash
start-all.bat
```

#### Linux/Mac
```bash
chmod +x start-all.sh
./start-all.sh
```

#### 手动启动

```bash
# 终端1: 启动后端
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 终端2: 启动执行引擎
cd executor
python main.py

# 终端3: 启动前端
cd frontend
npm run dev
```

### 访问

- 前端界面: http://localhost:3002
- 后端API: http://localhost:8000
- 执行引擎: http://localhost:8001
- API文档: http://localhost:8000/docs

## 功能模块

### 1. 设备管理
- 设备列表查看
- 设备状态监控
- 设备连接测试

### 2. 元素管理
- 元素定位管理
- 多定位符支持
- 元素复用

### 3. 步骤管理
- 步骤CRUD操作
- 多种操作类型
  - 设备操作: 点击、长按、输入、滑动、返回
  - 等待: 等待元素、等待时间
  - 断言: 文本断言、存在断言、颜色断言
  - 系统: 启动Activity、截图

### 4. 流程管理
- 标准流程: 步骤组合
- DSL流程: 领域特定语言
- Python流程: Python脚本

### 5. 用例管理
- 用例编排
- 三段式流程: Setup、Main、Teardown
- 参数配置

### 6. 套件管理
- 用例集合管理
- 批量执行
- 启用/禁用控制

### 7. 执行历史
- 执行记录
- 结果统计
- 日志查看

## 项目结构

```
testflow/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # API Schema
│   │   ├── routers/        # 路由
│   │   ├── repositories/   # 数据访问
│   │   └── main.py         # 应用入口
│   └── requirements.txt
│
├── executor/               # 执行引擎
│   ├── app/
│   │   ├── core/           # 核心逻辑
│   │   │   ├── executor.py      # 执行器
│   │   │   ├── task.py          # 任务模型
│   │   │   ├── execution_queue.py
│   │   │   └── step_executor.py
│   │   ├── services/       # 服务
│   │   │   ├── adb_service.py   # ADB服务
│   │   │   └── backend_client.py
│   │   ├── routers/        # API路由
│   │   └── main.py         # 应用入口
│   └── requirements.txt
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API服务
│   │   ├── components/     # 公共组件
│   │   └── App.tsx
│   └── package.json
│
├── start-all.bat           # Windows启动脚本
├── start-all.sh            # Linux/Mac启动脚本
└── README.md
```

## 开发指南

### 后端开发

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 执行引擎开发

```bash
cd executor
python main.py
```

### 前端开发

```bash
cd frontend
npm run dev
```

## 测试执行流程

1. **配置**: 在后端配置设备、元素、步骤
2. **编排**: 创建流程和用例
3. **执行**: 通过执行引擎执行测试
4. **查看**: 在前端查看执行结果

## API文档

### 后端API
- 基础路径: `http://localhost:8000/api/v1`
- 文档: `http://localhost:8000/docs`

### 执行引擎API
- 基础路径: `http://localhost:8001/api/v1`
- 文档: `http://localhost:8001/docs`

## License

MIT
