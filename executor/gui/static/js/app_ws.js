// WebSocket实时版本的应用逻辑
class WebSocketClient {
    constructor() {
        this.eventSource = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 3000; // 3秒

        // 缓存数据
        this.cachedTasks = [];
        this.cachedDevices = [];
        this.cachedLogs = [];

        this.initializeConnection();
        this.setupEventListeners();
    }

    initializeConnection() {
        console.log('🔗 初始化EventSource连接...');

        try {
            // 使用Server-Sent Events (SSE)连接
            this.eventSource = new EventSource('/ws');

            // 连接成功
            this.eventSource.onopen = () => {
                console.log('✅ EventSource连接成功');
                this.setConnectionStatus('connected');
                this.reconnectAttempts = 0;
            };

            // 监听消息
            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('解析消息失败:', error);
                }
            };

            // 连接错误
            this.eventSource.onerror = (error) => {
                console.error('❌ EventSource连接错误:', error);
                this.setConnectionStatus('disconnected');

                // 尝试重连
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`🔄 ${this.reconnectDelay/1000}秒后尝试第${this.reconnectAttempts}次重连...`);

                    setTimeout(() => {
                        this.close();
                        this.initializeConnection();
                    }, this.reconnectDelay);
                } else {
                    console.error('❌ 达到最大重连次数，停止重连');
                    this.setConnectionStatus('disconnected');
                }
            };

        } catch (error) {
            console.error('创建EventSource连接失败:', error);
            this.setConnectionStatus('disconnected');
        }
    }

    close() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    setConnectionStatus(status) {
        this.isConnected = (status === 'connected');
        const statusElement = document.getElementById('connectionStatus');
        const textElement = document.getElementById('connectionText');

        statusElement.className = `connection-status ${status}`;

        switch(status) {
            case 'connected':
                textElement.textContent = '已连接';
                break;
            case 'disconnected':
                textElement.textContent = '连接断开';
                break;
            case 'connecting':
                textElement.textContent = '连接中...';
                break;
        }
    }

    handleMessage(data) {
        console.log('📨 收到消息:', data.type);

        switch(data.type) {
            case 'connected':
                console.log('🎉 服务器连接确认');
                this.updateStatus(data.data);
                break;

            case 'status_update':
                console.log('📊 状态更新:', data.status);
                this.updateStatus(data);
                break;

            case 'task_update':
                console.log('📝 任务更新:', data.task_id);
                this.updateTask(data);
                break;

            case 'device_update':
                console.log('📱 设备更新:', data.devices?.length || 0);
                this.updateDevices(data.devices);
                break;

            case 'log':
                console.log('📋 新日志');
                this.addLog(data);
                break;

            case 'heartbeat':
                // 心跳消息，忽略
                break;

            default:
                console.log('❓ 未知消息类型:', data.type);
        }
    }

    updateStatus(data) {
        if (data.status) {
            const statusElement = document.getElementById('engineStatus');
            if (data.status === 'running') {
                statusElement.textContent = '运行中';
                statusElement.style.color = '#10b981';
            } else if (data.status === 'stopped') {
                statusElement.textContent = '已停止';
                statusElement.style.color = '#ef4444';
            } else {
                statusElement.textContent = data.status;
                statusElement.style.color = '#6b7280';
            }
        }

        if (data.active_tasks !== undefined) {
            document.getElementById('activeTasks').textContent = data.active_tasks;
        }

        if (data.queue_size !== undefined) {
            document.getElementById('queueSize').textContent = data.queue_size;
        }
    }

    updateTask(data) {
        const taskId = data.task_id;
        const taskData = data.data || {};

        // 查找并更新任务
        const existingIndex = this.cachedTasks.findIndex(t => t.id === taskId);

        if (existingIndex >= 0) {
            // 更新现有任务
            this.cachedTasks[existingIndex] = {
                ...this.cachedTasks[existingIndex],
                ...taskData,
                id: taskId
            };
        } else {
            // 添加新任务
            this.cachedTasks.push({
                id: taskId,
                ...taskData
            });
        }

        // 限制缓存大小
        if (this.cachedTasks.length > 50) {
            this.cachedTasks = this.cachedTasks.slice(-50);
        }

        this.renderTasks();
    }

    renderTasks() {
        const tasksList = document.getElementById('tasksList');

        if (this.cachedTasks.length === 0) {
            tasksList.innerHTML = '<div class="empty-state">暂无活动任务</div>';
            return;
        }

        tasksList.innerHTML = this.cachedTasks.map(task => `
            <div class="task-item">
                <div class="task-info">
                    <div class="task-name">任务 #${task.id}</div>
                    <div class="task-details">
                        类型: ${task.run_type || 'unknown'} | 设备: ${task.device_serial || 'N/A'}
                    </div>
                </div>
                <span class="task-status ${task.status || 'pending'}">
                    ${this.getTaskStatusText(task.status)}
                </span>
            </div>
        `).join('');

        // 自动滚动到底部
        tasksList.scrollTop = tasksList.scrollHeight;
    }

    updateDevices(devices) {
        if (!devices) return;

        this.cachedDevices = devices;
        document.getElementById('deviceCount').textContent = devices.length;

        const devicesList = document.getElementById('devicesList');

        if (devices.length === 0) {
            devicesList.innerHTML = '<div class="empty-state">暂无连接设备</div>';
            return;
        }

        devicesList.innerHTML = devices.map(device => `
            <div class="device-item">
                <div class="device-info">
                    <div class="device-name">${device.serial}</div>
                    <div class="device-details">状态: ${device.status}</div>
                </div>
                <span class="task-status ${device.status === 'device' ? 'completed' : 'pending'}">
                    ${device.status === 'device' ? '在线' : '离线'}
                </span>
            </div>
        `).join('');
    }

    addLog(data) {
        const logEntry = {
            timestamp: data.timestamp || new Date().toISOString(),
            level: data.level || 'INFO',
            module: data.module || 'system',
            message: data.message || ''
        };

        this.cachedLogs.push(logEntry);

        // 限制日志大小
        if (this.cachedLogs.length > 1000) {
            this.cachedLogs = this.cachedLogs.slice(-1000);
        }

        this.renderLog(logEntry);
    }

    renderLog(logEntry) {
        const logsContainer = document.getElementById('logsContainer');

        const logElement = document.createElement('div');
        logElement.className = 'log-entry';
        logElement.innerHTML = `
            <span class="timestamp">${this.formatTimestamp(logEntry.timestamp)}</span>
            <span class="level ${logEntry.level}">${logEntry.level}</span>
            <span class="message">${this.escapeHtml(logEntry.message)}</span>
        `;

        logsContainer.appendChild(logElement);

        // 自动滚动到底部
        logsContainer.scrollTop = logsContainer.scrollHeight;

        // 限制DOM元素数量
        while (logsContainer.children.length > 100) {
            logsContainer.removeChild(logsContainer.firstChild);
        }
    }

    formatTimestamp(timestamp) {
        try {
            const date = new Date(timestamp);
            return date.toLocaleTimeString('zh-CN', { hour12: false });
        } catch {
            return timestamp;
        }
    }

    getTaskStatusText(status) {
        const statusMap = {
            'pending': '待执行',
            'running': '执行中',
            'completed': '已完成',
            'failed': '失败',
            'cancelled': '已取消'
        };
        return statusMap[status] || status;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    setupEventListeners() {
        // 清空日志按钮
        document.getElementById('clearLogs').addEventListener('click', () => {
            this.cachedLogs = [];
            document.getElementById('logsContainer').innerHTML = '';
        });

        // 启动引擎按钮
        document.getElementById('startBtn').addEventListener('click', async () => {
            try {
                const response = await fetch('/api/start', { method: 'POST' });
                const data = await response.json();
                this.showNotification(data.message || '执行引擎启动中...', 'success');
            } catch (error) {
                this.showNotification('启动失败: ' + error.message, 'error');
            }
        });

        // 停止引擎按钮
        document.getElementById('stopBtn').addEventListener('click', async () => {
            try {
                const response = await fetch('/api/stop', { method: 'POST' });
                const data = await response.json();
                this.showNotification(data.message || '执行引擎停止中...', 'warning');
            } catch (error) {
                this.showNotification('停止失败: ' + error.message, 'error');
            }
        });
    }

    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#fbbf24' : '#3b82f6'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        // 3秒后自动消失
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 初始化WebSocket应用...');
    const app = new WebSocketClient();

    // 添加动画样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
});