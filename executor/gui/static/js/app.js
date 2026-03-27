// 应用状态
let refreshInterval = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    startAutoRefresh();
});

// 初始化应用
function initializeApp() {
    updateStatus();
    updateTasks();
    updateDevices();
    updateLogs();
}

// 设置事件监听器
function setupEventListeners() {
    // 启动引擎按钮
    document.getElementById('startBtn').addEventListener('click', async function() {
        try {
            const response = await fetch('/api/start', {
                method: 'POST'
            });
            const data = await response.json();
            showNotification(data.message || '执行引擎启动中...', 'success');
            setTimeout(updateStatus, 2000);
        } catch (error) {
            showNotification('启动失败: ' + error.message, 'error');
        }
    });

    // 停止引擎按钮
    document.getElementById('stopBtn').addEventListener('click', async function() {
        try {
            const response = await fetch('/api/stop', {
                method: 'POST'
            });
            const data = await response.json();
            showNotification(data.message || '执行引擎停止中...', 'warning');
            setTimeout(updateStatus, 2000);
        } catch (error) {
            showNotification('停止失败: ' + error.message, 'error');
        }
    });

    // 刷新任务按钮
    document.getElementById('refreshTasks').addEventListener('click', updateTasks);

    // 刷新设备按钮
    document.getElementById('refreshDevices').addEventListener('click', updateDevices);

    // 刷新日志按钮
    document.getElementById('refreshLogs').addEventListener('click', updateLogs);

    // 清空日志按钮
    document.getElementById('clearLogs').addEventListener('click', function() {
        document.getElementById('logsContainer').innerHTML = '';
    });
}

// 开始自动刷新
function startAutoRefresh() {
    // 每5秒刷新一次状态
    refreshInterval = setInterval(function() {
        updateStatus();
        updateTasks();
        updateDevices();
    }, 5000);

    // 每10秒刷新一次日志
    setInterval(updateLogs, 10000);
}

// 更新引擎状态
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.error) {
            document.getElementById('engineStatus').textContent = '错误';
            return;
        }

        // 更新引擎状态
        const statusElement = document.getElementById('engineStatus');
        if (data.status === 'running') {
            statusElement.textContent = '运行中';
            statusElement.style.color = '#10b981';
        } else {
            statusElement.textContent = '已停止';
            statusElement.style.color = '#ef4444';
        }

        // 更新其他状态
        document.getElementById('activeTasks').textContent = data.active_tasks || 0;
        document.getElementById('queueSize').textContent = data.queue_size || 0;

    } catch (error) {
        console.error('更新状态失败:', error);
        document.getElementById('engineStatus').textContent = '连接失败';
    }
}

// 更新任务列表
async function updateTasks() {
    try {
        const response = await fetch('/api/tasks');
        const data = await response.json();

        const tasksList = document.getElementById('tasksList');

        if (data.error || !data.tasks || data.tasks.length === 0) {
            tasksList.innerHTML = '<div class="empty-state">暂无活动任务</div>';
            return;
        }

        tasksList.innerHTML = data.tasks.map(task => `
            <div class="task-item">
                <div class="task-info">
                    <div class="task-name">任务 #${task.id}</div>
                    <div class="task-details">
                        类型: ${task.run_type} | 设备: ${task.device_serial || 'N/A'}
                    </div>
                </div>
                <span class="task-status ${task.status}">${getTaskStatusText(task.status)}</span>
            </div>
        `).join('');

    } catch (error) {
        console.error('更新任务失败:', error);
    }
}

// 更新设备列表
async function updateDevices() {
    try {
        const response = await fetch('/api/devices');
        const data = await response.json();

        const devicesList = document.getElementById('devicesList');

        if (data.error || !data.devices || data.devices.length === 0) {
            devicesList.innerHTML = '<div class="empty-state">暂无连接设备</div>';
            document.getElementById('deviceCount').textContent = '0';
            return;
        }

        document.getElementById('deviceCount').textContent = data.devices.length;

        devicesList.innerHTML = data.devices.map(device => `
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

    } catch (error) {
        console.error('更新设备失败:', error);
    }
}

// 更新日志
async function updateLogs() {
    try {
        const response = await fetch('/api/logs');
        const data = await response.json();

        const logsContainer = document.getElementById('logsContainer');

        if (data.error || !data.logs) {
            return;
        }

        logsContainer.innerHTML = data.logs.map(log => {
            // 解析日志行
            const match = log.match(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - (.+)/);
            if (match) {
                const [, timestamp, module, level, message] = match;
                return `
                    <div class="log-entry">
                        <span class="timestamp">${timestamp}</span>
                        <span class="level ${level}">${level}</span>
                        <span class="message">${escapeHtml(message)}</span>
                    </div>
                `;
            }
            return `<div class="log-entry">${escapeHtml(log)}</div>`;
        }).join('');

        // 滚动到底部
        logsContainer.scrollTop = logsContainer.scrollHeight;

    } catch (error) {
        console.error('更新日志失败:', error);
    }
}

// 获取任务状态文本
function getTaskStatusText(status) {
    const statusMap = {
        'pending': '待执行',
        'running': '执行中',
        'completed': '已完成',
        'failed': '失败',
        'cancelled': '已取消'
    };
    return statusMap[status] || status;
}

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
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

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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