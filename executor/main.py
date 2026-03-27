"""
TestFlow Execution Engine
独立的应用程序，通过数据库轮询执行任务
"""
import asyncio
import sys
import signal
import logging
from pathlib import Path
from app.core.executor import TestExecutor
from app.services.adb_service import ADBService
from app.core.config import settings

# 配置日志
class SafeFormatter(logging.Formatter):
    """安全的日志格式化器，处理Windows编码问题"""
    def format(self, record):
        try:
            return super().format(record)
        except UnicodeEncodeError:
            # 移除emoji等特殊字符
            message = record.getMessage()
            clean_message = message.encode('gbk', errors='ignore').decode('gbk')
            record.msg = clean_message
            return super().format(record)

# 设置控制台输出为UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('executor.log', encoding='utf-8')
    ]
)

# 设置格式化器
for handler in logging.root.handlers:
    handler.setFormatter(SafeFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)


class ExecutionEngineApp:
    """执行引擎应用程序"""

    def __init__(self):
        self.executor: TestExecutor = None
        self.adb_service: ADBService = None
        self.running = False
        self.shutdown_event = asyncio.Event()
        self.http_server = None
        self.registration_service = None

    async def initialize(self):
        """初始化执行引擎"""
        logger.info("🚀 初始化 TestFlow 执行引擎...")

        # 初始化ADB服务
        self.adb_service = ADBService()
        await self.adb_service.initialize()

        # 初始化执行器
        self.executor = TestExecutor(adb_service=self.adb_service)
        await self.executor.start()

        # 启动能力注册服务
        try:
            from app.services.capability_registration import init_registration_service
            import socket

            # 生成唯一的执行器ID
            hostname = socket.gethostname()
            executor_id = f"executor-{hostname}-{settings.executor_id_suffix}"

            self.registration_service = init_registration_service(
                backend_url=settings.backend_url,
                executor_id=executor_id,
                executor_version=settings.executor_version
            )
            await self.registration_service.start()
            logger.info(f"✅ 能力注册服务已启动: {executor_id}")
        except Exception as e:
            logger.warning(f"⚠️ 能力注册服务启动失败: {e}")

        # 启动HTTP服务器（供GUI连接）
        try:
            from app.core.http_server import ExecutorHTTPServer
            self.http_server = ExecutorHTTPServer(self.executor, host='127.0.0.1', port=5555)
            if self.http_server.start():
                logger.info("✅ HTTP服务器已启动，GUI可连接到 http://127.0.0.1:5555")
        except Exception as e:
            logger.warning(f"⚠️ HTTP服务器启动失败: {e}")

        logger.info("✅ 执行引擎初始化完成")

    async def shutdown(self):
        """关闭执行引擎"""
        logger.info("🛑 关闭执行引擎...")

        if self.registration_service:
            await self.registration_service.stop()

        if self.executor:
            await self.executor.stop()

        if self.adb_service:
            await self.adb_service.cleanup()

        logger.info("✅ 执行引擎已关闭")

    async def run(self):
        """运行执行引擎"""
        self.running = True
        logger.info("▶️  执行引擎开始运行...")
        logger.info(f"📊 并发数: {settings.max_concurrent_executions}")
        logger.info(f"⏱️  超时时间: {settings.execution_timeout}秒")
        logger.info("💡 按 Ctrl+C 停止执行引擎")

        # 注册信号处理
        if sys.platform != 'win32':
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self._handle_shutdown()))

        try:
            # 主循环 - 保持运行
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("⚠️  收到取消信号")
        finally:
            await self.shutdown()

    async def _handle_shutdown(self):
        """处理关闭信号"""
        logger.info("📨 收到关闭信号")
        self.running = False
        self.shutdown_event.set()


def print_banner():
    """打印启动横幅"""
    # 设置控制台编码为UTF-8（Windows）
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        TestFlow Execution Engine v1.0.0                   ║
║                                                           ║
║        Android 自动化测试执行引擎                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


async def main():
    """主函数"""
    print_banner()

    app = ExecutionEngineApp()

    try:
        await app.initialize()
        await app.run()
    except KeyboardInterrupt:
        logger.info("⌨️  用户中断")
    except Exception as e:
        logger.error(f"❌ 执行引擎异常: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 执行引擎已停止")
