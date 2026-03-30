# TestFlow

<div align="center">

**Android自动化测试平台**

支持UI自动化测试、流程编排、执行管理

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node-18+-green.svg)](https://nodejs.org/)

</div>

---

## 📋 项目简介

TestFlow是一个功能完整的Android自动化测试平台，采用前后端分离架构，提供可视化测试用例编排、实时执行监控和详细的结果分析功能。适用于移动应用自动化测试、回归测试、CI/CD集成等场景。

### 核心特性

- 🎯 **可视化测试编排** - 无代码创建测试用例，支持拖拽式流程设计
- 🔄 **多设备支持** - 同时管理多台Android设备，支持并行测试
- 📊 **实时监控** - WebSocket实时推送执行状态和日志
- 🔌 **灵活扩展** - 支持自定义Action类型和Python脚本
- 🤖 **AI辅助** - 集成AI服务，智能生成测试用例
- 📝 **完整报告** - 详细的测试报告和截图记录
- 🧪 **三段式流程** - Setup、Main、Teardown分离，提高复用性

## 🏗️ 系统架构

TestFlow采用三层架构设计：

```
┌─────────────────────────────────────────┐
│         Frontend (React + TS)           │
│         Port: 3002                       │
│  用户界面 | 测试管理 | 结果展示          │
└─────────────────────────────────────────┘
                   │
                   ↓ HTTP/WebSocket
┌─────────────────────────────────────────┐
│        Backend (FastAPI + SQLAlchemy)   │
│        Port: 8000                        │
│  API服务 | 数据管理 | 业务逻辑           │
└─────────────────────────────────────────┘
                   │
                   ↓ Database + HTTP
┌─────────────────────────────────────────┐
│         Executor (Python + ADB)         │
│         Port: 8001                       │
│  测试执行 | 设备控制 | 任务调度          │
└─────────────────────────────────────────┘
```

### 组件说明

| 组件 | 技术栈 | 端口 | 说明 |
|------|--------|------|------|
| **Frontend** | React + TypeScript + Vite + Ant Design | 3002 | Web前端界面 |
| **Backend** | FastAPI + SQLAlchemy + SQLite | 8000 | RESTful API服务 |
| **Executor** | Python + ADB + Appium | 8001 | 独立执行引擎 |

## 🚀 快速开始

### 环境要求

- **Python**: 3.9 或更高版本
- **Node.js**: 18 或更高版本
- **ADB**: Android Debug Bridge（Android SDK Platform Tools）
- **操作系统**: Windows / Linux / macOS

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/LSeaPDynasty/TestAgainFlow.git
cd TestAgainFlow/testflow

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt

# 3. 安装执行引擎依赖
cd ../executor
pip install -r requirements.txt

# 4. 安装前端依赖
cd ../frontend
npm install
```

### 启动服务

#### 方式一：使用启动脚本（推荐）

**Windows:**
```bash
start-all.bat
```

**Linux/macOS:**
```bash
chmod +x start-all.sh
./start-all.sh
```

#### 方式二：手动启动

```bash
# 终端1: 启动后端服务
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 终端2: 启动执行引擎
cd executor
python main.py

# 终端3: 启动前端
cd frontend
npm run dev
```

### 访问应用

- 🌐 **前端界面**: http://localhost:3002
- 🔌 **后端API**: http://localhost:8000
- 📖 **API文档**: http://localhost:8000/docs
- ⚙️ **执行引擎**: http://localhost:8001

## 📚 功能模块

### 1. 设备管理
- 📱 自动发现已连接的Android设备
- 📊 实时监控设备状态
- 🔌 支持多设备并发测试

### 2. 元素管理
- 🎯 多种定位方式（ID、XPath、文本等）
- 📦 元素库统一管理，支持复用
- 🔍 元素定位验证

### 3. 步骤管理
支持丰富的操作类型：

| 类别 | 操作 |
|------|------|
| **设备操作** | 点击、长按、输入文本、滑动、返回、Home |
| **等待** | 等待元素出现、等待时间 |
| **断言** | 文本断言、存在性断言、属性断言 |
| **系统** | 启动Activity、截图、获取设备信息 |
| **流程控制** | 循环、条件判断（DSL流程） |

### 4. 流程管理
- **标准流程**: 步骤组合，可视化编排
- **DSL流程**: 领域特定语言，支持复杂逻辑
- **Python流程**: 自由编写Python脚本

### 5. 用例管理
- 🧪 三段式结构：Setup（前置）+ Main（主体）+ Teardown（后置）
- 🔗 流程复用，提高效率
- ⚙️ 参数化配置

### 6. 测试套件
- 📦 用例集合管理
- 🔄 批量执行
- ✅ 启用/禁用控制

### 7. 执行与报告
- 📊 实时执行状态
- 📸 自动截图记录
- 📝 详细日志输出
- 📈 统计分析报告

## 📂 项目结构

```
testflow/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── models/            # ORM数据模型
│   │   ├── schemas/           # Pydantic Schema
│   │   ├── routers/           # API路由
│   │   ├── services/          # 业务逻辑
│   │   ├── repositories/      # 数据访问层
│   │   └── main.py            # FastAPI应用入口
│   ├── alembic/               # 数据库迁移
│   └── requirements.txt
│
├── executor/                  # 执行引擎
│   ├── app/
│   │   ├── core/              # 核心执行逻辑
│   │   │   ├── executor.py    # 主执行器
│   │   │   ├── step_executor.py  # 步骤执行
│   │   │   └── actions/       # 操作实现
│   │   ├── services/          # ADB、WebSocket等
│   │   └── drivers/           # 设备驱动
│   └── main.py                # 执行引擎入口
│
├── frontend/                  # 前端应用
│   ├── src/
│   │   ├── pages/             # 页面组件
│   │   ├── components/        # 公共组件
│   │   ├── services/          # API调用
│   │   └── App.tsx            # 应用入口
│   └── package.json
│
├── templates/                 # 测试模板
└── README.md
```

## 🛠️ 开发指南

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

### 运行测试

```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm test
```

## 📖 使用流程

```
┌─────────────┐
│  连接设备   │
└──────┬──────┘
       ↓
┌─────────────┐
│  配置元素   │ ← 创建/管理元素定位符
└──────┬──────┘
       ↓
┌─────────────┐
│  编排步骤   │ ← 创建可复用的测试步骤
└──────┬──────┘
       ↓
┌─────────────┐
│  组合流程   │ ← 将步骤组合成测试流程
└──────┬──────┘
       ↓
┌─────────────┐
│  创建用例   │ ← Setup + Main + Teardown
└──────┬──────┘
       ↓
┌─────────────┐
│  执行测试   │ ← 执行引擎运行测试
└──────┬──────┘
       ↓
┌─────────────┐
│  查看报告   │ ← 查看结果、日志、截图
└─────────────┘
```

## 🔧 技术栈

### 后端
- **框架**: FastAPI
- **ORM**: SQLAlchemy
- **数据库**: SQLite / MySQL / PostgreSQL
- **异步**: asyncio + uvicorn
- **WebSocket**: 实时通信

### 前端
- **框架**: React 18
- **语言**: TypeScript
- **构建**: Vite
- **UI库**: Ant Design
- **状态管理**: React Hooks + Context

### 执行引擎
- **ADB**: Android设备控制
- **Appium**: 元素定位（可选）
- **uiautomator2**: Android UI自动化

## 🤝 贡献

欢迎贡献代码、报告问题或提出新功能建议！

### 贡献流程

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用 **MIT License** 开源协议。

```
MIT License

Copyright (c) 2026 LSeaPDynasty

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 商业使用

本MIT许可证**允许商业使用**，您可以：

✅ 在商业项目中使用本软件
✅ 修改和定制源代码
✅ 将本软件集成到商业产品中
✅ 基于本软件开发商业解决方案

**唯一要求**:
- 保留原作者的版权声明和许可证声明
- 在您的产品中注明使用了本软件

## 📞 联系方式

- **作者**: LSeaPDynasty
- **仓库**: https://github.com/LSeaPDynasty/TestAgainFlow
- **问题反馈**: https://github.com/LSeaPDynasty/TestAgainFlow/issues

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

---

<div align="center">

**如果觉得项目有帮助，请给个 ⭐ Star 支持一下！**

Made with ❤️ by LSeaPDynasty

</div>
