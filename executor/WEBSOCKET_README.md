# TestFlow 执行引擎 WebSocket GUI 使用指南

## 🚀 简介

TestFlow 执行引擎现在支持**实时WebSocket连接**版本！通过WebSocket技术，GUI界面可以实时接收后端的更新，无需手动刷新。

## ✨ 主要特性

### 🔴 实时更新
- **零延迟**: 后端变化立即推送到前端
- **自动重连**: 网络中断时自动尝试重连
- **状态指示**: 实时显示连接状态

### 📊 实时监控
- **任务状态**: 任务执行状态实时更新
- **设备状态**: 设备连接状态实时监控
- **日志推送**: 系统日志实时推送显示
- **引擎状态**: 执行引擎运行状态实时显示

### 🎯 技术优势
- **Server-Sent Events (SSE)**: 使用SSE实现服务器推送
- **WebSocket客户端**: executor通过WebSocket连接后端
- **异步处理**: 所有通信都是异步非阻塞的
- **自动重连**: 智能重连机制，最多10次重试

## 🛠️ 架构说明

```
┌─────────────┐         WebSocket          ┌─────────────┐
│             │ ◄────────────────────────────▶ │             │
│  Executor   │                             │  Backend    │
│     GUI     │                             │   Server    │
│             │ ◄────── SSE ────────────────── │             │
└─────────────┘         (前端)              └─────────────┘
      ▲                                        ▲
      │                                        │
      │ 浏览器                                  │
      │                                        │
┌─────┴─────┐                            ┌────┴─────┐
│  Browser  │                            │ Database │
│   (SSE)   │                            │          │
└───────────┘                            └──────────┘
```

### 连接流程
1. **Backend API** 启动WebSocket服务器 (`ws://localhost:8000/ws/executor`)
2. **Executor GUI** 启动WebSocket客户端连接到Backend
3. **Browser** 通过SSE连接到Executor GUI (`http://localhost:5000/ws`)
4. **实时通信**: Backend → Executor GUI → Browser

## 📦 安装依赖

### Backend依赖
```bash
cd backend
pip install websockets
```

### Executor依赖
```bash
cd executor
pip install websockets flask flask-cors
```

## 🚀 快速开始

### 方法1: 使用批处理文件（Windows推荐）

双击运行 `start_gui_ws.bat` 文件：

```bash
start_gui_ws.bat
```

### 方法2: 使用Python命令

在executor目录下运行：

```bash
python start_gui_ws.py
```

### 方法3: 自定义后端地址

如果后端不在默认地址 `ws://localhost:8000`：

```bash
python start_gui_ws.py --backend-url ws://192.168.1.100:8000
```

## 🌐 访问界面

启动成功后，浏览器会自动打开 `http://127.0.0.1:5000`

## 📋 界面说明

### 连接状态指示器
- **🟢 已连接**: 绿色，表示所有连接正常
- **🟡 连接中**: 黄色，正在尝试连接
- **🔴 连接断开**: 红色，连接已断开，正在尝试重连

### 实时更新标识
带有"实时连接"或"实时更新"标识的面板会自动更新数据，无需手动刷新。

## 🔧 配置选项

### 后端WebSocket地址
默认连接到 `ws://localhost:8000`，可以通过以下方式修改：

**命令行参数**:
```bash
python start_gui_ws.py --backend-url ws://192.168.1.100:8000
```

**代码修改**:
```python
# 在 start_gui_ws.py 中
server = ExecutorWebServerWS(backend_url="ws://your-backend:8000")
```

### Web服务器端口
默认端口为 `5000`，可以修改：

**命令行参数**:
```bash
python start_gui_ws.py --port 8080
```

### 重连设置
在 `gui/websocket_client.py` 中可以修改重连参数：

```python
self.reconnect_delay = 5  # 重连延迟（秒）
self.max_reconnect_attempts = 10  # 最大重连次数
```

## 🔌 API接口

### Backend WebSocket端点

#### 连接端点
```
ws://localhost:8000/ws/executor
```

#### 消息类型

**客户端发送的消息**:
```json
{
  "type": "ping",           // 心跳
  "type": "subscribe",      // 订阅
  "type": "get_status"      // 获取状态
}
```

**服务器发送的消息**:
```json
{
  "type": "connected",       // 连接成功
  "type": "status_update",   // 状态更新
  "type": "task_update",     // 任务更新
  "type": "log",             // 日志
  "type": "device_update",   // 设备更新
  "type": "pong",            // 心跳响应
  "type": "error"            // 错误
}
```

### GUI REST API端点

传统的REST API仍然可用，用于手动获取数据：

```
GET /api/status    # 获取状态
GET /api/tasks     # 获取任务列表
GET /api/devices   # 获取设备列表
GET /api/logs      # 获取日志
POST /api/start    # 启动引擎
POST /api/stop     # 停止引擎
```

## 🐛 故障排除

### 问题1: 无法连接到后端WebSocket
**错误信息**: `WebSocket connection failed`

**解决方案**:
1. 确认后端API服务器已启动
2. 检查后端地址是否正确
3. 检查防火墙设置
4. 查看后端日志确认WebSocket服务已启动

### 问题2: 前端SSE连接失败
**错误信息**: `EventSource connection failed`

**解决方案**:
1. 确认Executor GUI服务器已启动
2. 检查浏览器控制台错误信息
3. 确认端口5000未被占用

### 问题3: 数据不更新
**可能原因**:
- WebSocket连接已断开
- 后端没有发送更新消息

**解决方案**:
1. 检查连接状态指示器
2. 查看浏览器控制台日志
3. 重启Executor GUI

### 问题4: 频繁断线重连
**可能原因**:
- 网络不稳定
- 后端服务器负载过高

**解决方案**:
1. 检查网络连接
2. 增加重连延迟时间
3. 优化后端性能

## 🔍 调试模式

### 启用详细日志

修改 `start_gui_ws.py`:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 浏览器控制台

按F12打开浏览器开发者工具，查看Console标签页的日志：

```javascript
// 所有关键操作都会在控制台显示
🔗 初始化EventSource连接...
✅ EventSource连接成功
📨 收到消息: status_update
📊 状态更新: running
```

## 📊 性能优化

### 减少日志数量
在 `gui/web_server_ws.py` 中限制日志存储：

```python
# 限制日志大小
if len(self.logs_data) > 500:  # 从1000改为500
    self.logs_data = self.logs_data[-500:]
```

### 调整心跳频率
在 `gui/websocket_client.py` 中修改心跳间隔：

```python
self.websocket = await websockets.connect(
    self.ws_url,
    ping_interval=30,  # 从20改为30秒
    ping_timeout=30
)
```

## 🔐 安全建议

⚠️ **重要提示**:
- 当前实现仅用于开发环境
- 生产环境需要添加认证机制
- 考虑使用WSS (WebSocket Secure) 而不是WS
- 实施消息加密和签名
- 添加访问控制和速率限制

## 📚 相关文档

- [普通版本GUI使用指南](GUI_README.md)
- [执行引擎文档](README.md)
- [后端API文档](../backend/README.md)

## 🆚 版本对比

| 特性 | 普通版本 | WebSocket版本 |
|------|----------|---------------|
| 数据更新方式 | 定时轮询 | 实时推送 |
| 延迟 | 5-10秒 | <1秒 |
| 服务器负载 | 较高 | 较低 |
| 网络流量 | 较多 | 较少 |
| 实现复杂度 | 简单 | 中等 |
| 可靠性 | 高 | 中等（依赖网络） |

## 🎉 总结

WebSocket版本的GUI提供了真正的实时体验，适合需要即时反馈的场景。选择哪个版本取决于你的具体需求：

- **普通版本**: 简单可靠，适合一般监控
- **WebSocket版本**: 实时性好，适合需要即时更新的场景

享受实时更新的TestFlow执行引擎GUI体验！ 🚀