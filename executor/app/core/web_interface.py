"""
执行引擎内置Web服务器
直接监控和控制执行引擎，不依赖后端WebSocket
"""
import os
import sys
import json
import logging
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS

logger = logging.getLogger(__name__)


class ExecutorWebInterface:
    """执行引擎内置Web界面"""

    def __init__(self, executor):
        """
        初始化Web界面
        :param executor: TestExecutor实例
        """
        self.executor = executor
        self.app = Flask(__name__,
                        template_folder='gui/templates',
                        static_folder='gui/static')
        CORS(self.app)

        self.is_running = False
        self._setup_routes()

    def _setup_routes(self):
        """设置路由"""

        @self.app.route('/')
        def index():
            """主页面"""
            return render_template('index.html')

        @self.app.route('/api/status')
        def get_status():
            """获取执行引擎状态 - 直接从executor读取"""
            status = {
                'status': 'running' if self.executor.is_running else 'stopped',
                'concurrent': self.executor.execution_queue.maxsize if self.executor.execution_queue else 0,
                'timeout': 3600,  # 从配置读取
                'active_tasks': len(self.executor.active_tasks),
                'queue_size': self.executor.execution_queue.qsize() if self.executor.execution_queue else 0,
                'uptime': str(datetime.now()) if self.executor.is_running else 'N/A'
            }
            return jsonify(status)

        @self.app.route('/api/tasks')
        def get_tasks():
            """获取活动任务列表 - 直接从executor读取"""
            tasks = []
            for task_id, task in self.executor.active_tasks.items():
                task_info = {
                    'id': task_id,
                    'status': task.status.value if hasattr(task.status, 'value') else str(task.status),
                    'run_type': getattr(task, 'execution_type', 'unknown'),
                    'target_id': getattr(task, 'target_id', 0),
                    'device_serial': getattr(task, 'device_serial', 'N/A'),
                    'created_at': str(getattr(task, 'created_at', 'N/A'))
                }
                tasks.append(task_info)

            return jsonify({'tasks': tasks})

        @self.app.route('/api/devices')
        def get_devices():
            """获取连接的设备列表"""
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

            return jsonify({'devices': devices})

        @self.app.route('/api/logs')
        def get_logs():
            """获取执行引擎日志"""
            log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'executor.log')
            logs = []

            try:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        logs = lines[-100:] if len(lines) > 100 else lines
            except Exception as e:
                logger.error(f"读取日志失败: {e}")

            return jsonify({'logs': logs})

        @self.app.route('/api/start', methods=['POST'])
        def start_executor():
            """启动执行引擎"""
            try:
                if self.executor.is_running:
                    return jsonify({'message': '执行引擎已在运行'})

                # 在新线程中启动执行引擎
                def start_engine():
                    try:
                        asyncio.run(self.executor.start())
                    except Exception as e:
                        logger.error(f"启动执行引擎失败: {e}")

                threading.Thread(target=start_engine, daemon=True).start()

                return jsonify({'message': '正在启动执行引擎...'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/stop', methods=['POST'])
        def stop_executor():
            """停止执行引擎"""
            try:
                if not self.executor.is_running:
                    return jsonify({'message': '执行引擎未启动'})

                # 在新线程中停止执行引擎
                def stop_engine():
                    try:
                        asyncio.run(self.executor.stop())
                    except Exception as e:
                        logger.error(f"停止执行引擎失败: {e}")

                threading.Thread(target=stop_engine, daemon=True).start()

                return jsonify({'message': '正在停止执行引擎...'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

        @self.app.route('/ws')
        def websocket_endpoint():
            """SSE endpoint for real-time updates"""
            return self._handle_sse()

    def _handle_sse(self):
        """处理SSE连接"""
        def generate():
            try:
                # 发送初始状态
                initial_status = {
                    'status': 'running' if self.executor.is_running else 'stopped',
                    'active_tasks': len(self.executor.active_tasks),
                    'queue_size': self.executor.execution_queue.qsize() if self.executor.execution_queue else 0
                }
                yield f"data: {json.dumps({'type': 'connected', 'data': initial_status})}\n\n"

                # 推送实时更新
                while self.is_running:
                    try:
                        # 定期发送状态更新
                        status_update = {
                            'type': 'status_update',
                            'status': 'running' if self.executor.is_running else 'stopped',
                            'data': {
                                'active_tasks': len(self.executor.active_tasks),
                                'queue_size': self.executor.execution_queue.qsize() if self.executor.execution_queue else 0
                            }
                        }
                        yield f"data: {json.dumps(status_update)}\n\n"

                        # 发送心跳
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"

                        time.sleep(2)  # 每2秒更新一次

                    except GeneratorExit:
                        break
                    except Exception as e:
                        logger.error(f"SSE发送错误: {e}")
                        break

            except GeneratorExit:
                logger.info("前端SSE连接关闭")

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )

    def start(self, host='127.0.0.1', port=5000, blocking=False):
        """启动Web界面"""
        self.is_running = True

        if blocking:
            logger.info(f"🌐 启动执行引擎Web界面: http://{host}:{port}")
            self.app.run(host=host, port=port, debug=False, threaded=True)
        else:
            # 在新线程中启动Web服务器
            def run_server():
                logger.info(f"🌐 启动执行引擎Web界面: http://{host}:{port}")
                self.app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)

            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()
            return thread

    def stop(self):
        """停止Web界面"""
        self.is_running = False