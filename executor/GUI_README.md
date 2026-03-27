# TestFlow 执行引擎 GUI 使用指南

## 简介

TestFlow 执行引擎现在配备了一个现代化的Web GUI界面，方便监控和管理Android自动化测试执行过程。

## 功能特性

### 📊 实时监控
- **引擎状态**: 实时显示执行引擎运行状态
- **活动任务**: 显示当前正在执行的任务列表
- **队列状态**: 显示待执行任务的队列大小
- **设备状态**: 显示连接的Android设备列表

### 🎛️ 控制功能
- **启动引擎**: 一键启动测试执行引擎
- **停止引擎**: 安全停止正在运行的引擎
- **刷新数据**: 手动刷新各个模块的数据

### 📋 日志查看
- **实时日志**: 显示系统运行日志
- **自动更新**: 日志内容自动刷新
- **高亮显示**: 不同级别的日志用不同颜色显示

## 快速开始

### 方法1: 使用批处理文件（Windows推荐）

双击运行 `start_gui.bat` 文件：

```bash
start_gui.bat
```

### 方法2: 使用Python命令

在executor目录下运行：

```bash
python start_gui.py
```

### 方法3: 使用虚拟环境

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 启动GUI
python start_gui.py
```

## 访问界面

启动成功后，浏览器会自动打开 `http://127.0.0.1:5000`

如果没有自动打开，手动在浏览器中访问上述地址。

## 界面说明

### 1. 头部区域
- **Logo和版本号**: 显示应用名称和版本
- **控制按钮**: 启动/停止引擎的控制按钮

### 2. 状态卡片
- **引擎状态**: 显示引擎当前状态（运行中/已停止）
- **活动任务**: 当前正在执行的任务数量
- **队列大小**: 等待执行的任务数量
- **连接设备**: 已连接的Android设备数量

### 3. 任务列表
显示所有活动任务的详细信息：
- 任务ID
- 任务类型（testcase/suite）
- 设备序列号
- 执行状态

### 4. 设备列表
显示所有连接的Android设备：
- 设备序列号
- 连接状态
- 设备型号

### 5. 系统日志
显示引擎运行日志：
- 时间戳
- 日志级别（INFO/WARNING/ERROR）
- 日志消息
- 彩色高亮显示

## API接口

GUI界面通过以下REST API与执行引擎通信：

### 获取状态
```http
GET /api/status
```

### 获取任务列表
```http
GET /api/tasks
```

### 获取设备列表
```http
GET /api/devices
```

### 获取日志
```http
GET /api/logs
```

### 启动引擎
```http
POST /api/start
```

### 停止引擎
```http
POST /api/stop
```

## 技术栈

- **后端**: Flask + Flask-CORS
- **前端**: 原生JavaScript + HTML5 + CSS3
- **通信**: REST API
- **实时更新**: 定时轮询机制

## 配置说明

### 端口配置
默认端口为 `5000`，可以在 `gui/web_server.py` 中修改：

```python
server.run(host='127.0.0.1', port=5000, debug=False)
```

### 自动刷新间隔
- 状态和任务列表: 每5秒刷新一次
- 日志内容: 每10秒刷新一次

可以在 `gui/static/js/app.js` 中修改刷新频率：

```javascript
// 每5秒刷新一次状态
refreshInterval = setInterval(function() {
    updateStatus();
    updateTasks();
    updateDevices();
}, 5000);

// 每10秒刷新一次日志
setInterval(updateLogs, 10000);
```

## 故障排除

### 问题1: 端口被占用
**错误信息**: `Address already in use`

**解决方案**:
1. 检查是否有其他程序占用了5000端口
2. 修改web_server.py中的端口号
3. 或者关闭占用端口的程序

### 问题2: 浏览器无法访问
**错误信息**: `无法访问此网站`

**解决方案**:
1. 检查防火墙设置
2. 确认服务器已正常启动
3. 尝试使用 `http://localhost:5000` 而不是 `http://127.0.0.1:5000`

### 问题3: API调用失败
**错误信息**: 控制台显示API错误

**解决方案**:
1. 检查执行引擎是否正常启动
2. 查看浏览器控制台的错误信息
3. 确认CORS设置正确

## 开发说明

### 目录结构
```
executor/
├── gui/
│   ├── web_server.py       # Flask Web服务器
│   ├── templates/          # HTML模板
│   │   └── index.html     # 主页面
│   ├── static/            # 静态资源
│   │   ├── css/
│   │   │   └── style.css  # 样式文件
│   │   └── js/
│   │       └── app.js     # 前端逻辑
│   └── __init__.py
├── start_gui.py           # GUI启动脚本
├── start_gui.bat          # Windows批处理启动脚本
└── requirements.txt       # 依赖包列表
```

### 扩展功能
可以通过修改以下文件来扩展功能：

1. **添加新的API端点**: 在 `gui/web_server.py` 中添加路由
2. **修改界面样式**: 编辑 `gui/static/css/style.css`
3. **添加新功能**: 在 `gui/static/js/app.js` 中添加JavaScript代码
4. **修改页面布局**: 编辑 `gui/templates/index.html`

## 安全建议

⚠️ **重要提示**:
- 当前GUI仅用于开发环境
- 不要在生产环境中使用默认配置
- 建议添加身份验证机制
- 考虑使用HTTPS而不是HTTP
- 限制访问IP地址范围

## 反馈与支持

如有问题或建议，请通过以下方式联系：

- 查看项目文档: `README.md`
- 查看执行引擎文档: `executor/README.md`
- 提交Issue或Pull Request

---

**享受使用TestFlow执行引擎的GUI界面！** 🚀