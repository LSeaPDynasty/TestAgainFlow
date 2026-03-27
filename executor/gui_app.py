"""
执行引擎GUI程序
使用Tkinter创建独立的GUI应用，直接连接到执行引擎
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import json
import threading
import time
from datetime import datetime

class ExecutorGUI:
    """执行引擎GUI主窗口"""

    def __init__(self, executor_url="http://localhost:5555"):
        self.executor_url = executor_url
        self.root = tk.Tk()
        self.root.title("TestFlow 执行引擎控制台")
        self.root.geometry("1000x700")

        # 设置样式
        self.setup_styles()

        # 创建界面
        self.create_widgets()

        # 启动自动刷新
        self.auto_refresh()

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 按钮样式
        style.configure('Success.TButton',
                       background='#10b981',
                       foreground='white',
                       font=('Arial', 10, 'bold'))
        style.configure('Danger.TButton',
                       background='#ef4444',
                       foreground='white',
                       font=('Arial', 10, 'bold'))

    def create_widgets(self):
        """创建界面组件"""
        # 顶部控制面板
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)

        # 标题
        title_label = ttk.Label(control_frame,
                               text="🤖 TestFlow 执行引擎控制台",
                               font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT, padx=10)

        # 控制按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.RIGHT)

        self.start_btn = ttk.Button(button_frame, text="▶️ 启动引擎",
                                   command=self.start_executor,
                                   style='Success.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(button_frame, text="⏹️ 停止引擎",
                                  command=self.stop_executor,
                                  style='Danger.TButton')
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.refresh_btn = ttk.Button(button_frame, text="🔄 刷新",
                                     command=self.refresh_status)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)

        # 状态面板
        status_frame = ttk.LabelFrame(self.root, text="引擎状态", padding="10")
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        # 状态卡片
        cards_frame = ttk.Frame(status_frame)
        cards_frame.pack(fill=tk.X)

        self.status_vars = {
            'engine_status': tk.StringVar(value="检查中..."),
            'active_tasks': tk.StringVar(value="0"),
            'queue_size': tk.StringVar(value="0"),
            'device_count': tk.StringVar(value="0")
        }

        cards = [
            ("引擎状态", self.status_vars['engine_status']),
            ("活动任务", self.status_vars['active_tasks']),
            ("队列大小", self.status_vars['queue_size']),
            ("连接设备", self.status_vars['device_count'])
        ]

        for i, (label, var) in enumerate(cards):
            card_frame = ttk.Frame(cards_frame, borderwidth=2, relief="groove")
            card_frame.grid(row=0, column=i, padx=5, sticky="nsew")

            ttk.Label(card_frame, text=label, font=('Arial', 9)).pack(pady=5)
            ttk.Label(card_frame, textvariable=var, font=('Arial', 14, 'bold')).pack(pady=5)

        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.columnconfigure(2, weight=1)
        cards_frame.columnconfigure(3, weight=1)

        # 主内容区域
        content_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 左侧：任务列表
        tasks_frame = ttk.LabelFrame(content_frame, text="活动任务", padding="10")
        content_frame.add(tasks_frame, weight=1)

        self.tasks_list = ttk.Treeview(tasks_frame,
                                       columns=('ID', '类型', '设备', '状态'),
                                       show='headings',
                                       height=10)
        self.tasks_list.heading('ID', text='任务ID')
        self.tasks_list.heading('类型', text='类型')
        self.tasks_list.heading('设备', text='设备')
        self.tasks_list.heading('状态', text='状态')

        self.tasks_list.column('ID', width=200)
        self.tasks_list.column('类型', width=100)
        self.tasks_list.column('设备', width=150)
        self.tasks_list.column('状态', width=100)

        self.tasks_list.pack(fill=tk.BOTH, expand=True)

        # 右侧：设备列表
        devices_frame = ttk.LabelFrame(content_frame, text="连接的设备", padding="10")
        content_frame.add(devices_frame, weight=1)

        self.devices_list = ttk.Treeview(devices_frame,
                                        columns=('序列号', '状态'),
                                        show='headings',
                                        height=10)
        self.devices_list.heading('序列号', text='设备序列号')
        self.devices_list.heading('状态', text='状态')

        self.devices_list.column('序列号', width=250)
        self.devices_list.column('状态', width=100)

        self.devices_list.pack(fill=tk.BOTH, expand=True)

        # 底部：日志面板
        log_frame = ttk.LabelFrame(self.root, text="系统日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 日志控制
        log_control = ttk.Frame(log_frame)
        log_control.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(log_control, text="清空日志",
                  command=self.clear_logs).pack(side=tk.RIGHT)

        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                  height=10,
                                                  font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 配置标签颜色
        self.log_text.tag_configure('INFO', foreground='black')
        self.log_text.tag_configure('WARNING', foreground='orange')
        self.log_text.tag_configure('ERROR', foreground='red')

    def start_executor(self):
        """启动执行引擎"""
        try:
            response = requests.post(f"{self.executor_url}/api/start", timeout=5)
            data = response.json()
            messagebox.showinfo("启动", data.get('message', '执行引擎启动中...'))
            self.refresh_status()
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {str(e)}")

    def stop_executor(self):
        """停止执行引擎"""
        try:
            response = requests.post(f"{self.executor_url}/api/stop", timeout=5)
            data = response.json()
            messagebox.showinfo("停止", data.get('message', '执行引擎停止中...'))
            self.refresh_status()
        except Exception as e:
            messagebox.showerror("错误", f"停止失败: {str(e)}")

    def refresh_status(self):
        """刷新状态"""
        def update():
            try:
                # 获取状态
                response = requests.get(f"{self.executor_url}/api/status", timeout=3)
                status = response.json()

                # 更新状态显示
                self.status_vars['engine_status'].set(
                    '运行中' if status.get('status') == 'running' else '已停止'
                )
                self.status_vars['active_tasks'].set(str(status.get('active_tasks', 0)))
                self.status_vars['queue_size'].set(str(status.get('queue_size', 0)))

                # 更新任务列表
                response = requests.get(f"{self.executor_url}/api/tasks", timeout=3)
                tasks_data = response.json()

                # 清空现有任务
                for item in self.tasks_list.get_children():
                    self.tasks_list.delete(item)

                # 添加任务
                for task in tasks_data.get('tasks', []):
                    self.tasks_list.insert('', 'end', values=(
                        task.get('id', ''),
                        task.get('run_type', ''),
                        task.get('device_serial', 'N/A'),
                        task.get('status', '')
                    ))

                # 更新设备列表
                response = requests.get(f"{self.executor_url}/api/devices", timeout=3)
                devices_data = response.json()

                self.status_vars['device_count'].set(
                    str(len(devices_data.get('devices', [])))
                )

                # 清空现有设备
                for item in self.devices_list.get_children():
                    self.devices_list.delete(item)

                # 添加设备
                for device in devices_data.get('devices', []):
                    self.devices_list.insert('', 'end', values=(
                        device.get('serial', ''),
                        device.get('status', '')
                    ))

                # 更新日志
                response = requests.get(f"{self.executor_url}/api/logs", timeout=3)
                logs_data = response.json()

                # 清空日志
                self.log_text.delete(1.0, tk.END)

                # 添加日志
                for log in logs_data.get('logs', []):
                    self.log_text.insert(tk.END, log)

                self.log_text.see(tk.END)

            except Exception as e:
                self.log_text.insert(tk.END, f"刷新失败: {str(e)}\n")
                self.log_text.see(tk.END)

        # 在后台线程中更新
        thread = threading.Thread(target=update, daemon=True)
        thread.start()

    def clear_logs(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def auto_refresh(self):
        """自动刷新"""
        self.refresh_status()
        # 每5秒自动刷新一次
        self.root.after(5000, self.auto_refresh)

    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    """主函数"""
    import sys

    # 允许通过命令行参数指定执行引擎URL
    executor_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5555"

    app = ExecutorGUI(executor_url)
    app.run()


if __name__ == '__main__':
    main()