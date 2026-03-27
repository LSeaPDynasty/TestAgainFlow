"""
Flask Web Server for Executor GUI
为执行引擎提供Web界面，通过WebSocket连接后端接收实时更新
"""
import os
import sys
import json
import logging
import websockets
import asyncio
from datetime import datetime
from threading import Thread, Event
from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS
from queue import Queue
import time

logger = logging.getLogger(__name__)


class BackendWebSocketClient:
    """连接到后端WebSocket的客户端"""

    def __init__(self, backend_url="ws://localhost:8000"):
        self.backend_url = backend_url
        self.ws_url = f"{backend_url}/ws/executor"
        self.websocket = None
        self.is_connected = False
        self.message_queue = Queue()
        self.stop_event = Event()
        self.event_loop = None

        # 存储最新的数据
        self.status_data = {
            'status': 'disconnected',
            'concurrent': 5,
            'timeout': 3600,
            'active_tasks': 0,
            'queue_size': 0
        }
        self.tasks_data = []
        self.devices_data = []
        self.logs_data = []

    async def connect(self):
        """连接到后端WebSocket"""
        try:
            logger.info(f"🔗 连接到后端WebSocket: {self.ws_url}")
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=20
            )
            self.is_connected = True
            logger.info("✅ 已连接到后端WebSocket")

            # 启动消息接收
            asyncio.create_task(self._receive_messages())
            return True

        except Exception as e:
            logger.error(f"❌ 连接后端WebSocket失败: {e}")
            self.is_connected = False
            return False

    async def _receive_messages(self):
        """接收消息"""
        try:
            async for message in self.websocket:
                if self.stop_event.is_set():
                    break

                try:
                    data = json.loads(message)
                    self._handle_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"解析JSON失败: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️ 后端WebSocket连接关闭")
            self.is_connected = False
        except Exception as e:
            logger.error(f"接收消息错误: {e}")
            self.is_connected = False

    def _handle_message(self, data):
        """处理收到的消息"""
        message_type = data.get("type")

        if message_type == "connected":
            logger.info(f"🎉 {data.get('message')}")

        elif message_type == "status_update":
            self.status_data.update(data.get("data", {}))
            self.status_data['status'] = data.get("status", "unknown")
            self.message_queue.put(data)

        elif message_type == "task_update":
            task_id = data.get("task_id")
            task_data = data.get("data", {})

            # 更新或添加任务
            updated = False
            for i, task in enumerate(self.tasks_data):
                if task.get('id') == task_id:
                    self.tasks_data[i] = {**task, **task_data, 'id': task_id}
                    updated = True
                    break

            if not updated:
                self.tasks_data.append({'id': task_id, **task_data})

            # 限制数量
            if len(self.tasks_data) > 50:
                self.tasks_data = self.tasks_data[-50:]

            self.message_queue.put(data)

        elif message_type == "device_update":
            self.devices_data = data.get("devices", [])
            self.message_queue.put(data)

        elif message_type == "log":
            log_entry = {
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'level': data.get('level', 'INFO'),
                'module': data.get('module', 'system'),
                'message': data.get('message', '')
            }
            self.logs_data.append(log_entry)

            # 限制日志数量
            if len(self.logs_data) > 1000:
                self.logs_data = self.logs_data[-1000:]

            self.message_queue.put(data)

    async def disconnect(self):
        """断开连接"""
        self.stop_event.set()
        if self.websocket:
            await self.websocket.close()
        self.is_connected = False

    def run_in_thread(self):
        """在新线程中运行"""
        async def run():
            while not self.stop_event.is_set():
                if not self.is_connected:
                    if not await self.connect():
                        await asyncio.sleep(5)
                        continue

                await asyncio.sleep(1)

            await self.disconnect()

        def start_loop():
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            self.event_loop.run_until_complete(run())

        thread = Thread(target=start_loop, daemon=True)
        thread.start()


class ExecutorWebServer:
    """执行引擎Web服务器"""

    def __init__(self, backend_url="ws://localhost:8000"):
        self.app = Flask(__name__,
                        template_folder='templates',
                        static_folder='static')
        CORS(self.app)

        self.backend_client = BackendWebSocketClient(backend_url)
        self.is_running = False

        self._setup_routes()

    def _setup_routes(self):
        """设置路由"""

        @self.app.route('/')
        def index():
            """主页面"""
            return render_template('index_ws.html')

        @self.app.route('/api/status')
        def get_status():
            """获取执行引擎状态"""
            return jsonify(self.backend_client.status_data)

        @self.app.route('/api/tasks')
        def get_tasks():
            """获取活动任务列表"""
            return jsonify({'tasks': self.backend_client.tasks_data})

        @self.app.route('/api/logs')
        def get_logs():
            """获取最近的日志"""
            return jsonify({'logs': self.backend_client.logs_data[-100:]})

        @self.app.route('/api/devices')
        def get_devices():
            """获取连接的设备列表"""
            return jsonify({'devices': self.backend_client.devices_data})

        @self.app.route('/ws')
        def websocket_endpoint():
            """SSE endpoint for frontend"""
            return self._handle_sse()

        @self.app.route('/api/start', methods=['POST'])
        def start_executor():
            """启动执行引擎（模拟）"""
            return jsonify({
                'message': '执行引擎应该作为独立进程启动。请使用: python main.py'
            })

        @self.app.route('/api/stop', methods=['POST'])
        def stop_executor():
            """停止执行引擎（模拟）"""
            return jsonify({
                'message': '执行引擎应该在独立进程中停止。使用 Ctrl+C'
            })

    def _handle_sse(self):
        """处理SSE连接"""
        def generate():
            try:
                # 发送初始状态
                yield f"data: {json.dumps({'type': 'connected', 'data': self.backend_client.status_data})}\n\n"

                # 推送实时更新
                while self.is_running:
                    try:
                        # 从队列获取消息
                        message = self.backend_client.message_queue.get(timeout=1)
                        yield f"data: {json.dumps(message)}\n\n"
                    except:
                        # 发送心跳
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()})}\n\n"

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

    def start(self, host='127.0.0.1', port=5000, debug=False):
        """启动Web服务器"""
        self.is_running = True

        # 启动后端WebSocket客户端
        self.backend_client.run_in_thread()

        logger.info(f"🌐 启动Web服务器: http://{host}:{port}")
        logger.info(f"🔗 连接到后端: {self.backend_client.backend_url}")

        try:
            self.app.run(host=host, port=port, debug=debug, threaded=True)
        finally:
            self.is_running = False

    def stop(self):
        """停止Web服务器"""
        self.is_running = False


def main():
    """主函数"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    server = ExecutorWebServer(backend_url="ws://localhost:8000")
    server.start(host='127.0.0.1', port=5000, debug=False)


if __name__ == '__main__':
    main()