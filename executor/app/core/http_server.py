"""
执行引擎内置HTTP服务器
提供简单的API接口供GUI程序连接
"""
import logging
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import asyncio

logger = logging.getLogger(__name__)


class ExecutorAPIHandler(BaseHTTPRequestHandler):
    """处理来自GUI的HTTP请求"""

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # 获取状态
        if path == '/api/status':
            self.send_json_response(self.get_executor_status())
        # 获取任务列表
        elif path == '/api/tasks':
            self.send_json_response(self.get_tasks())
        # 获取设备列表
        elif path == '/api/devices':
            self.send_json_response(self.get_devices())
        # 获取日志
        elif path == '/api/logs':
            self.send_json_response(self.get_logs())
        else:
            self.send_json_response({'error': 'Not found'}, 404)

    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # 启动执行引擎
        if path == '/api/start':
            response = self.start_executor()
            self.send_json_response(response)
        # 停止执行引擎
        elif path == '/api/stop':
            response = self.stop_executor()
            self.send_json_response(response)
        else:
            self.send_json_response({'error': 'Not found'}, 404)

    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response.encode('utf-8'))

    def get_executor_status(self):
        """获取执行引擎状态"""
        executor = self.server.executor

        return {
            'status': 'running' if executor.is_running else 'stopped',
            'concurrent': 5,  # 从配置读取
            'timeout': 3600,
            'active_tasks': len(executor.active_tasks),
            'queue_size': executor.execution_queue.qsize() if executor.execution_queue else 0
        }

    def get_tasks(self):
        """获取任务列表"""
        executor = self.server.executor
        tasks = []

        for task_id, task in executor.active_tasks.items():
            task_info = {
                'id': task_id,
                'status': task.status.value if hasattr(task.status, 'value') else str(task.status),
                'run_type': getattr(task, 'execution_type', 'unknown'),
                'target_id': getattr(task, 'target_id', 0),
                'device_serial': getattr(task, 'device_serial', 'N/A'),
                'created_at': str(getattr(task, 'created_at', 'N/A'))
            }
            tasks.append(task_info)

        return {'tasks': tasks}

    def get_devices(self):
        """获取设备列表"""
        devices = []
        try:
            import subprocess
            result = subprocess.run(['adb', 'devices'],
                                 capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            devices.append({
                                'serial': parts[0],
                                'status': parts[1]
                            })
        except Exception as e:
            logger.error(f"获取设备列表失败: {e}")

        return {'devices': devices}

    def get_logs(self):
        """获取日志"""
        import os
        log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'executor.log')
        logs = []

        try:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    logs = lines[-100:] if len(lines) > 100 else lines
        except Exception as e:
            logger.error(f"读取日志失败: {e}")

        return {'logs': logs}

    def start_executor(self):
        """启动执行引擎"""
        executor = self.server.executor

        if executor.is_running:
            return {'message': '执行引擎已在运行'}

        # 在新线程中启动
        def start():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(executor.start())
            except Exception as e:
                logger.error(f"启动执行引擎失败: {e}")

        threading.Thread(target=start, daemon=True).start()
        return {'message': '正在启动执行引擎...'}

    def stop_executor(self):
        """停止执行引擎"""
        executor = self.server.executor

        if not executor.is_running:
            return {'message': '执行引擎未启动'}

        # 在新线程中停止
        def stop():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(executor.stop())
            except Exception as e:
                logger.error(f"停止执行引擎失败: {e}")

        threading.Thread(target=stop, daemon=True).start()
        return {'message': '正在停止执行引擎...'}

    def log_message(self, format, *args):
        """禁用默认日志"""
        pass


class ExecutorHTTPServer:
    """执行引擎HTTP服务器"""

    def __init__(self, executor, host='127.0.0.1', port=5555):
        self.executor = executor
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None

    def start(self):
        """启动HTTP服务器"""
        try:
            # 创建服务器
            self.server = HTTPServer((self.host, self.port), ExecutorAPIHandler)
            self.server.executor = self.executor

            # 在新线程中运行服务器
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()

            logger.info(f"🌐 执行引擎HTTP服务器启动: http://{self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"启动HTTP服务器失败: {e}")
            return False

    def stop(self):
        """停止HTTP服务器"""
        if self.server:
            self.server.shutdown()
            logger.info("🌐 执行引擎HTTP服务器已停止")