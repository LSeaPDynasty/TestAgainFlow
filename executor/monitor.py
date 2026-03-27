"""
执行引擎监控GUI
纯查看界面，显示引擎状态、日志、任务进度等，无操作功能
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
import threading
import time
from datetime import datetime

class ExecutorMonitor:
    """执行引擎监控窗口"""

    def __init__(self, executor_url="http://localhost:5555"):
        self.executor_url = executor_url
        self.root = tk.Tk()
        self.root.title("TestFlow 执行引擎监控")
        self.root.geometry("1200x800")

        # 设置不可调整大小（纯监控界面）
        self.root.resizable(True, True)

        # 创建界面
        self.create_widgets()

        # 启动自动刷新
        self.is_monitoring = True
        self.auto_refresh()

    def create_widgets(self):
        """创建界面组件"""
        # 顶部标题栏
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(title_frame,
                              text="🤖 TestFlow 执行引擎监控",
                              font=("Arial", 18, "bold"),
                              bg="#2c3e50",
                              fg="white")
        title_label.pack(pady=15)

        # 状态指示器
        self.status_indicator = tk.Label(title_frame,
                                        text="● 连接中...",
                                        font=("Arial", 12),
                                        bg="#2c3e50",
                                        fg="#f39c12")
        self.status_indicator.pack(side=tk.RIGHT, padx=20)

        # 主要内容区域
        main_frame = tk.Frame(self.root, bg="#ecf0f1")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 状态卡片区域
        cards_frame = tk.Frame(main_frame, bg="#ecf0f1")
        cards_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_vars = {
            'engine_status': tk.StringVar(value="检查中..."),
            'backend_status': tk.StringVar(value="检查中..."),
            'active_tasks': tk.StringVar(value="0"),
            'completed_tasks': tk.StringVar(value="0"),
            'queue_size': tk.StringVar(value="0"),
            'device_count': tk.StringVar(value="0"),
            'uptime': tk.StringVar(value="00:00:00")
        }

        # 创建状态卡片
        cards = [
            ("引擎状态", self.status_vars['engine_status'], "#3498db"),
            ("后端连接", self.status_vars['backend_status'], "#9b59b6"),
            ("活动任务", self.status_vars['active_tasks'], "#e74c3c"),
            ("已完成", self.status_vars['completed_tasks'], "#27ae60"),
            ("队列大小", self.status_vars['queue_size'], "#f39c12"),
            ("连接设备", self.status_vars['device_count'], "#1abc9c"),
            ("运行时间", self.status_vars['uptime'], "#34495e")
        ]

        for i, (title, var, color) in enumerate(cards):
            card = tk.Frame(cards_frame, bg="white", relief="raised", bd=2)
            card.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="nsew")

            tk.Label(card, text=title, font=("Arial", 10), bg="#ecf0f1", fg="#7f8c8d").pack(pady=(5, 2))

            value_label = tk.Label(card, textvariable=var, font=("Arial", 16, "bold"), bg="white", fg=color)
            value_label.pack(pady=(0, 5))

        for i in range(4):
            cards_frame.columnconfigure(i, weight=1)

        # 中间区域 - 左右分栏
        content_frame = tk.PanedWindow(main_frame, orient=tk.HORIZONTAL, bg="#ecf0f1")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧：任务列表
        left_frame = tk.Frame(content_frame, bg="white")
        content_frame.add(left_frame, minsize=400)

        tk.Label(left_frame, text="📋 当前任务", font=("Arial", 12, "bold"), bg="white").pack(pady=10)

        # 任务列表
        task_columns = ('任务ID', '类型', '目标ID', '设备', '状态', '进度')
        self.tasks_tree = ttk.Treeview(left_frame, columns=task_columns, show='headings', height=15)

        for col in task_columns:
            self.tasks_tree.heading(col, text=col)
            self.tasks_tree.column(col, width=100)

        # 添加滚动条
        task_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=task_scrollbar.set)

        self.tasks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        task_scrollbar.pack(side=tk.LEFT, fill=tk.Y, pady=10, padx=(0, 10))

        # 右侧：设备列表和日志
        right_frame = tk.Frame(content_frame, bg="white")
        content_frame.add(right_frame, minsize=400)

        # 设备列表
        tk.Label(right_frame, text="📱 连接的设备", font=("Arial", 12, "bold"), bg="white").pack(pady=10)

        device_columns = ('序列号', '状态', '型号', 'Android版本')
        self.devices_tree = ttk.Treeview(right_frame, columns=device_columns, show='headings', height=8)

        for col in device_columns:
            self.devices_tree.heading(col, text=col)
            self.devices_tree.column(col, width=100)

        device_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.devices_tree.yview)
        self.devices_tree.configure(yscrollcommand=device_scrollbar.set)

        self.devices_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        device_scrollbar.pack(side=tk.LEFT, fill=tk.Y, pady=(0, 10), padx=(0, 10))

        # 日志区域
        log_frame = tk.Frame(right_frame, bg="white")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(log_frame, text="📋 系统日志", font=("Arial", 12, "bold"), bg="white").pack(anchor="w")

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, font=("Consolas", 9), bg="#2c3e50", fg="#ecf0f1")
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # 配置日志颜色
        self.log_text.tag_configure('INFO', foreground='#3498db')
        self.log_text.tag_configure('WARNING', foreground='#f39c12')
        self.log_text.tag_configure('ERROR', foreground='#e74c3c')
        self.log_text.tag_configure('SUCCESS', foreground='#27ae60')
        self.log_text.tag_configure('TIMESTAMP', foreground='#95a5a6')

        # 底部状态栏
        status_bar = tk.Frame(self.root, bg="#bdc3c7", height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)

        self.last_update = tk.StringVar(value="最后更新: --")
        tk.Label(status_bar, textvariable=self.last_update, bg="#bdc3c7", fg="#2c3e50").pack(side=tk.LEFT, padx=10)

        self.refresh_rate = tk.StringVar(value="刷新间隔: 3秒")
        tk.Label(status_bar, textvariable=self.refresh_rate, bg="#bdc3c7", fg="#2c3e50").pack(side=tk.RIGHT, padx=10)

    def update_status(self):
        """更新状态显示"""
        try:
            # 获取引擎状态
            response = requests.get(f"{self.executor_url}/api/status", timeout=5)
            response.raise_for_status()  # 检查HTTP错误
            status = response.json()

            # 更新状态变量
            engine_status = status.get('status', 'unknown')
            self.status_vars['engine_status'].set(
                '🟢 运行中' if engine_status == 'running' else '🔴 已停止'
            )
            self.status_vars['active_tasks'].set(str(status.get('active_tasks', 0)))
            self.status_vars['queue_size'].set(str(status.get('queue_size', 0)))

            # 检查后端连接状态（从执行引擎获取）
            backend_connected = status.get('backend_connected', True)
            self.status_vars['backend_status'].set(
                '🟢 已连接' if backend_connected else '🔴 断开'
            )

            # 更新任务列表
            try:
                response = requests.get(f"{self.executor_url}/api/tasks", timeout=5)
                response.raise_for_status()
                tasks_data = response.json()

                # 清空现有任务
                for item in self.tasks_tree.get_children():
                    self.tasks_tree.delete(item)

                # 添加任务
                completed_count = 0
                for task in tasks_data.get('tasks', []):
                    task_status = task.get('status', '')
                    if task_status in ['completed', 'passed']:
                        completed_count += 1

                    self.tasks_tree.insert('', 'end', values=(
                        task.get('id', ''),
                        task.get('run_type', ''),
                        task.get('target_id', ''),
                        task.get('device_serial', 'N/A'),
                        task_status,
                        '100%' if task_status in ['completed', 'passed'] else '0%'
                    ))

                self.status_vars['completed_tasks'].set(str(completed_count))

            except Exception as e:
                print(f"获取任务列表失败: {e}")

            # 更新设备列表
            try:
                response = requests.get(f"{self.executor_url}/api/devices", timeout=5)
                response.raise_for_status()
                devices_data = response.json()

                self.status_vars['device_count'].set(str(len(devices_data.get('devices', []))))

                # 清空现有设备
                for item in self.devices_tree.get_children():
                    self.devices_tree.delete(item)

                # 添加设备
                for device in devices_data.get('devices', []):
                    self.devices_tree.insert('', 'end', values=(
                        device.get('serial', ''),
                        device.get('status', ''),
                        'Unknown',  # 型号信息需要额外获取
                        'Unknown'   # Android版本需要额外获取
                    ))

            except Exception as e:
                print(f"获取设备列表失败: {e}")

            # 更新连接状态
            self.status_indicator.config(text="● 已连接", fg="#27ae60")

            # 更新时间戳
            self.last_update.set(f"最后更新: {datetime.now().strftime('%H:%M:%S')}")

        except requests.exceptions.RequestException as e:
            # 连接失败
            print(f"连接失败: {e}")
            self.status_indicator.config(text="● 连接断开", fg="#e74c3c")
            self.status_vars['engine_status'].set('🔴 连接断开')
            self.status_vars['backend_status'].set('🔴 无法连接')
            self.last_update.set(f"最后更新: {datetime.now().strftime('%H:%M:%S')} (失败)")

        except Exception as e:
            # 其他错误
            print(f"更新状态错误: {e}")
            self.status_indicator.config(text="● 错误", fg="#e74c3c")
            self.last_update.set(f"最后更新: {datetime.now().strftime('%H:%M:%S')} (错误)")

    def update_logs(self):
        """更新日志显示"""
        try:
            response = requests.get(f"{self.executor_url}/api/logs", timeout=2)
            logs_data = response.json()

            # 只在有新日志时更新
            current_log_count = int(self.log_text.index('end-1c').split('.')[0])
            new_logs = logs_data.get('logs', [])

            if len(new_logs) > current_log_count:
                # 清空并重新显示日志
                self.log_text.delete(1.0, tk.END)

                for log in new_logs[-50:]:  # 只显示最后50条
                    # 解析日志级别
                    log_str = str(log).strip()
                    if 'ERROR' in log_str:
                        tag = 'ERROR'
                    elif 'WARNING' in log_str:
                        tag = 'WARNING'
                    elif 'INFO' in log_str:
                        tag = 'INFO'
                    elif '✅' in log_str or 'passed' in log_str.lower():
                        tag = 'SUCCESS'
                    else:
                        tag = 'INFO'

                    self.log_text.insert(tk.END, log_str + '\n', tag)

                # 自动滚动到底部
                self.log_text.see(tk.END)

        except Exception as e:
            pass  # 日志更新失败不影响主界面

    def auto_refresh(self):
        """自动刷新"""
        if self.is_monitoring:
            self.update_status()
            self.update_logs()

            # 每3秒刷新一次
            self.root.after(3000, self.auto_refresh)

    def run(self):
        """运行监控界面"""
        # 首次更新
        self.update_status()

        # 启动主循环
        self.root.mainloop()

    def stop(self):
        """停止监控"""
        self.is_monitoring = False


def main():
    """主函数"""
    import sys

    # 允许通过命令行参数指定执行引擎URL
    executor_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5555"

    try:
        monitor = ExecutorMonitor(executor_url)
        monitor.run()
    except KeyboardInterrupt:
        print("\n监控界面已关闭")


if __name__ == '__main__':
    main()