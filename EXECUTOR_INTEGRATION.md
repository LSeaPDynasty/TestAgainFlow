# 执行引擎状态集成文档

## 🎯 功能说明

现在前端设备管理页面可以从后端获取正在运行的执行引擎信息，包括：

### 📊 执行引擎状态
- **连接状态**: 显示是否有执行引擎连接到后端
- **活跃引擎数**: 当前连接的执行引擎数量
- **正在使用设备**: 正在被执行引擎使用的设备数量
- **活动任务**: 当前正在执行的任务数量

### 📱 设备状态增强
- **使用标识**: 显示哪些设备正在被执行引擎使用
- **绿色标签**: "运行中"标签标识正在使用的设备
- **保护机制**: 正在使用的设备无法删除

## 🔧 技术实现

### 后端API

#### 1. 执行引擎状态API
```
GET /api/v1/executor/status
```

返回：
```json
{
  "connected": true,
  "active_executors": 1,
  "executors": [
    {
      "id": "executor_xxx",
      "status": "connected",
      "connected_at": "2024-03-20T12:00:00",
      "last_heartbeat": "2024-03-20T12:05:00",
      "active_tasks": 2,
      "queue_size": 5
    }
  ]
}
```

#### 2. 执行引擎设备API
```
GET /api/v1/executor/devices
```

返回：
```json
{
  "total": 3,
  "devices": [
    {
      "id": 1,
      "name": "测试机01",
      "serial": "FJLQ2412443432YD",
      "status": "online",
      "in_use": true,
      "current_executor": "executor_xxx"
    }
  ],
  "in_use_count": 1
}
```

#### 3. 活动任务API
```
GET /api/v1/executor/tasks
```

返回：
```json
{
  "total": 2,
  "tasks": [
    {
      "task_id": "run_1",
      "executor_id": "executor_xxx",
      "status": "running",
      "run_type": "testcase",
      "target_id": 123,
      "device_serial": "FJLQ2412443432YD"
    }
  ]
}
```

### WebSocket通信

执行引擎通过WebSocket连接到后端：
```
ws://localhost:8000/ws/executor
```

#### 执行引擎发送的消息类型

1. **状态更新**
```json
{
  "type": "status_update",
  "status": "running",
  "data": {
    "active_tasks": 2,
    "queue_size": 1
  }
}
```

2. **任务更新**
```json
{
  "type": "task_update",
  "task_id": "run_1",
  "data": {
    "status": "running",
    "device_serial": "FJLQ2412443432YD"
  }
}
```

3. **心跳**
```json
{
  "type": "ping"
}
```

## 🚀 使用流程

### 1. 启动后端API服务器
```bash
cd C:\Users\lsea.yu\Desktop\docs\testflow\backend
python run.py
```

后端会启动：
- REST API服务器 (http://localhost:8000)
- WebSocket服务器 (ws://localhost:8000/ws/executor)

### 2. 启动执行引擎
```bash
cd C:\Users\lsea.yu\Desktop\docs\testflow\executor
python main.py
```

执行引擎会：
- 连接到数据库
- 连接到后端WebSocket
- 启动HTTP服务器 (http://127.0.0.1:5555)
- 开始轮询任务

### 3. 打开前端界面
```bash
cd C:\Users\lsea.yu\Desktop\docs\testflow\frontend
npm run dev
```

访问 http://localhost:5173，进入设备管理页面。

## 📱 界面显示

### 执行引擎状态卡片
```
┌─────────────────────────────────────────┐
│ ⚡ 执行引擎状态                         │
├─────────────────────────────────────────┤
│                                         │
│  ● 连接状态    ✅ 已连接                │
│  🚀 活跃引擎    1 个                    │
│  ⏰ 正在使用设备 1 个                   │
│  ⚡ 活动任务    2 个                    │
│                                         │
└─────────────────────────────────────────┘
```

### 设备卡片
```
┌───────────────────────────┐
│ 🏷️ 使用中                 │ ← 绿色ribbon
│ 测试机01  ● online  🚀运行中│
├───────────────────────────┤
│ 序列号: FJLQ2412443432YD   │
│ 型号: Pixel 5              │
│ 连接类型: USB              │
│                           │
│ [测试连接]                │
└───────────────────────────┘
```

## 🔄 数据流

```
执行引擎 (Python)
    │
    │ WebSocket (ws://localhost:8000/ws/executor)
    │
    ↓
后端API (FastAPI)
    │
    │ REST API (/api/v1/executor/*)
    │
    ↓
前端Web界面 (React)
```

## ⚙️ 配置说明

### 自动刷新间隔

**执行引擎状态**: 每5秒刷新
```typescript
refetchInterval: 5000
```

**设备列表**: 每10秒刷新
```typescript
refetchInterval: 10000
```

### 自定义刷新间隔

在 `src/pages/Devices/index.tsx` 中修改：

```typescript
const { data: executorData } = useQuery({
  queryKey: ['executor-status'],
  queryFn: () => getExecutorStatus(),
  refetchInterval: 3000, // 改为3秒
});
```

## 🐛 故障排除

### 问题1: 执行引擎状态显示"未连接"

**原因**: 执行引擎未启动或WebSocket连接失败

**解决方案**:
1. 检查执行引擎是否正在运行
2. 查看执行引擎日志，确认WebSocket连接成功
3. 确认后端API服务器正在运行

### 问题2: 设备不显示"使用中"状态

**原因**: 执行引擎未发送任务更新消息

**解决方案**:
1. 确认执行引擎有活动任务
2. 检查WebSocket消息是否正确发送
3. 查看后端日志，确认任务状态更新

### 问题3: 状态不更新

**原因**: 前端轮询间隔过长或WebSocket断开

**解决方案**:
1. 减少刷新间隔
2. 检查网络连接
3. 查看浏览器控制台错误信息

## 📝 开发说明

### 添加新的状态显示

1. 在后端 `executor_status.py` 中添加新的数据
2. 在前端添加相应的查询
3. 在页面中显示新数据

### 自定义状态卡片

在 `Devices/index.tsx` 中修改状态卡片布局：

```typescript
<Row gutter={16}>
  <Col span={8}>
    <Statistic title="自定义指标" value={value} />
  </Col>
  // 添加更多统计卡片
</Row>
```

## 🎉 总结

现在前端设备管理页面已经完全集成执行引擎状态：

✅ 实时显示执行引擎连接状态
✅ 显示正在使用的设备
✅ 自动刷新，数据实时更新
✅ 用户友好的界面和标识

通过这个集成，用户可以在设备管理页面清楚地看到哪些设备正在被执行引擎使用，避免冲突和资源竞争！