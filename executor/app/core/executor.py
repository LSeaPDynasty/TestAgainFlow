"""
Test Execution Engine Core (Refactored)
管理测试执行生命周期 - 主调度器
职责：
- 任务调度和队列管理
- 协调各个服务
- 生命周期管理
"""
import asyncio
import logging
from typing import Dict, Optional, Any

from .config import settings
from ..services.adb_service import ADBService
from ..services.db_client import DatabaseClient
from ..services.websocket_client import ExecutorWebSocketClient
from ..services.task_queue_client import TaskQueueClient
from .execution_queue import ExecutionQueue
from .task import ExecutionTask, TaskStatus, TaskResult, ExecutionType
from ..utils.backend_log_handler import BackendLogHandler
from .services import LogService, ResultCollector, ExecutionService

logger = logging.getLogger(__name__)


class TestExecutor:
    """
    主测试执行器（重构版）

    职责：
    1. 任务调度和队列管理
    2. 协调ExecutionService、LogService、ResultCollector
    3. 生命周期管理

    不再包含：
    - 具体的执行逻辑（已移到ExecutionService）
    - 重复的日志发送（已移到LogService）
    - 结果聚合（已移到ResultCollector）
    """

    def __init__(self, adb_service: ADBService, backend_ws_url: str = "ws://localhost:8000"):
        # 基础服务
        self.adb_service = adb_service
        self.db_client = DatabaseClient()
        self.execution_queue = ExecutionQueue(max_size=settings.max_concurrent_executions)
        self.active_tasks: Dict[str, ExecutionTask] = {}
        self.is_running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._poller_task: Optional[asyncio.Task] = None

        # WebSocket和任务队列客户端
        self.ws_client = ExecutorWebSocketClient(backend_ws_url)
        self.task_queue_client = TaskQueueClient(backend_ws_url)

        # ✅ 新增：使用专门的服务
        self.log_service = LogService(self.task_queue_client)
        self.result_collector = ResultCollector()
        self.execution_service = ExecutionService(
            self.db_client,
            self.log_service,
            self.result_collector
        )

        # 设备自动发现
        from ..services.device_discovery import DeviceAutoDiscovery
        self.device_discovery = DeviceAutoDiscovery(self.ws_client)

        # 后端日志处理器
        self.backend_log_handler: Optional[BackendLogHandler] = None

    async def start(self):
        """启动执行引擎"""
        if self.is_running:
            logger.warning("⚠️  执行引擎已在运行")
            return

        self.is_running = True
        logger.info("🚀 启动执行引擎（重构版）")

        # 连接数据库
        await self.db_client.connect()

        # 连接到后端WebSocket
        await self.ws_client.connect()

        # 连接到任务队列
        await self.task_queue_client.connect()

        # 初始化后端日志处理器
        self.backend_log_handler = BackendLogHandler(self.task_queue_client)
        self.backend_log_handler.setLevel(logging.INFO)
        self.backend_log_handler.setFormatter(logging.Formatter('%(message)s'))

        # 添加到根 logger
        root_logger = logging.getLogger()
        root_logger.addHandler(self.backend_log_handler)

        # 发送启动状态
        await self.ws_client.send_status_update("running", {
            "concurrent": settings.max_concurrent_executions,
            "timeout": settings.execution_timeout
        })

        # 启动设备自动发现
        self._discovery_task = asyncio.create_task(self.device_discovery.start_background_scan())

        # 启动工作线程
        self._worker_task = asyncio.create_task(self._worker())

        # 启动任务队列监听
        self._poller_task = asyncio.create_task(self._listen_task_queue())

        logger.info("✅ 执行引擎启动完成")

    async def stop(self):
        """停止执行引擎"""
        if not self.is_running:
            return

        logger.info("🛑 停止执行引擎")
        self.is_running = False

        # 取消任务
        if self._worker_task:
            self._worker_task.cancel()
        if self._poller_task:
            self._poller_task.cancel()
        if hasattr(self, '_discovery_task') and self._discovery_task:
            self._discovery_task.cancel()

        # 等待任务完成
        try:
            await asyncio.gather(self._worker_task, self._poller_task, return_exceptions=True)
        except Exception:
            pass

        # 关闭连接
        await self.ws_client.close()
        await self.task_queue_client.close()
        await self.db_client.close()

        logger.info("✅ 执行引擎已停止")

    async def _worker(self):
        """工作线程 - 从队列中取任务并执行"""
        while self.is_running:
            try:
                # 从队列获取任务（阻塞等待）
                task = await self.execution_queue.get()

                if task is None:
                    # 停止信号
                    break

                logger.info(f"📋 从队列获取任务: {task.task_id} ({task.execution_type})")

                # 执行任务
                await self._execute_task(task)

            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)

    async def _listen_task_queue(self):
        """监听任务队列 - 从后端获取新任务"""
        while self.is_running:
            try:
                # 从后端获取待执行任务
                tasks = await self.task_queue_client.fetch_tasks()

                if tasks:
                    logger.info(f"📥 从后端获取 {len(tasks)} 个任务")

                    for task_info in tasks:
                        task = ExecutionTask.from_dict(task_info)

                        # 添加到执行队列
                        await self.execution_queue.put(task)

                        # 记录活跃任务
                        self.active_tasks[task.task_id] = task

                        # 发送任务状态
                        await self.task_queue_client.update_task_status(
                            task.task_id,
                            "running",
                            {"started_at": asyncio.get_event_loop().time()}
                        )

                # 等待一段时间再轮询
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Task queue listener error: {e}", exc_info=True)
                await asyncio.sleep(5)  # 出错后等待5秒再重试

    async def _execute_task(self, task: ExecutionTask):
        """执行任务 - 调用ExecutionService"""
        task_id = task.task_id
        set_current_task_id(task_id)

        try:
            logger.info(f"▶️  开始执行任务: {task_id} ({task.execution_type})")
            await self.log_service.info(task_id, f"开始执行任务: {task.execution_type}")

            # 重置结果收集器
            self.result_collector.reset()

            # 根据类型分发任务
            if task.execution_type == ExecutionType.STEP:
                result = await self.execution_service.execute_step(task)
            elif task.execution_type == ExecutionType.FLOW:
                result = await self.execution_service.execute_flow(task)
            elif task.execution_type == ExecutionType.TESTCASE:
                result = await self._execute_testcase(task)
            elif task.execution_type == ExecutionType.SUITE:
                result = await self._execute_suite(task)
            elif task.execution_type == ExecutionType.TEST_PLAN:
                result = await self._execute_test_plan(task)
            else:
                await self.log_service.error(task_id, f"未知的执行类型: {task.execution_type}")
                result = TaskResult.FAILED

            # 更新任务状态
            status = "completed" if result != TaskResult.FAILED else "failed"
            await self.task_queue_client.update_task_status(task_id, status, {
                "result": result.value,
                "summary": self.result_collector.get_summary()
            })

            logger.info(f"✅ 任务执行完成: {task_id} - {result.value}")

        except Exception as e:
            logger.error(f"Task execution error: {e}", exc_info=True)
            await self.log_service.error(task_id, f"任务执行异常: {str(e)}")

            await self.task_queue_client.update_task_status(task_id, "failed", {
                "error": str(e)
            })

        finally:
            # 清理
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            clear_current_task_id()

    async def _execute_testcase(self, task: ExecutionTask) -> TaskResult:
        """执行测试用例"""
        try:
            # 获取测试用例数据
            testcase_data = await self.db_client.get_testcase(task.target_id)
            if not testcase_data:
                await self.log_service.error(task.task_id, f"用例不存在: {task.target_id}")
                return TaskResult.FAILED

            await self.log_service.info(task.task_id, f"📝 执行用例: {testcase_data.get('name', 'Unknown')}")

            # 执行Main阶段
            testcase_items = testcase_data.get("testcase_items", [])
            if not testcase_items:
                await self.log_service.warning(task.task_id, "测试用例没有步骤")
                return TaskResult.SKIPPED

            result = await self.execution_service.execute_testcase_items(task, testcase_items)

            return result

        except Exception as e:
            logger.error(f"Testcase execution error: {e}", exc_info=True)
            await self.log_service.error(task.task_id, f"测试用例执行异常: {str(e)}")
            return TaskResult.FAILED

    async def _execute_suite(self, task: ExecutionTask) -> TaskResult:
        """执行套件（多个用例）"""
        suite_data = await self.db_client.get_suite(task.target_id)

        if not suite_data:
            error_msg = f"套件不存在: {task.target_id}"
            await self.log_service.error(task.task_id, error_msg)
            raise ValueError(error_msg)

        suite_name = suite_data.get('name', 'Unknown')
        testcases = suite_data.get("testcases", [])

        logger.info(f"执行套件: {suite_name} ({len(testcases)} 个用例)")
        await self.log_service.info(task.task_id, f"开始执行套件: {suite_name} ({len(testcases)} 个用例)")

        passed = 0
        failed = 0
        skipped = 0

        for idx, testcase_info in enumerate(testcases, 1):
            if not testcase_info.get("enabled", 1):
                logger.info(f"用例 {idx}/{len(testcases)}: 跳过（已禁用）")
                await self.log_service.warning(task.task_id, f"用例 {idx}/{len(testcases)} 跳过（已禁用）: {testcase_info.get('name', 'Unknown')}")
                skipped += 1
                continue

            testcase_name = testcase_info.get('name', 'Unknown')
            logger.info(f"用例 {idx}/{len(testcases)}: {testcase_name}")

            # 发送用例开始日志（包含用例ID，便于前端聚合）
            await self.log_service.info(task.task_id, f"用例 {idx}/{len(testcases)}: {testcase_name}", extra={
                "testcase_id": testcase_info.get('testcase_id'),
                "testcase_name": testcase_name,
                "testcase_index": idx,
                "testcase_total": len(testcases)
            })

            testcase_task = ExecutionTask(
                task_id=f"{task.task_id}_tc_{testcase_info['id']}",
                execution_type=ExecutionType.TESTCASE,
                target_id=testcase_info["testcase_id"],
                device_serial=task.device_serial,
                config=task.config
            )

            result = await self._execute_testcase(testcase_task)

            if result == TaskResult.PASSED:
                passed += 1
                logger.info(f"用例通过: {testcase_name}")
                await self.log_service.info(task.task_id, f"用例 {idx}/{len(testcases)} 通过: {testcase_name}", extra={
                    "testcase_id": testcase_info.get('testcase_id'),
                    "testcase_name": testcase_name,
                    "testcase_result": "passed"
                })
            elif result == TaskResult.FAILED:
                failed += 1
                logger.error(f"用例失败: {testcase_name}")
                await self.log_service.error(task.task_id, f"用例 {idx}/{len(testcases)} 失败: {testcase_name}", extra={
                    "testcase_id": testcase_info.get('testcase_id'),
                    "testcase_name": testcase_name,
                    "testcase_result": "failed"
                })
            else:
                skipped += 1
                logger.warning(f"用例跳过: {testcase_name}")
                await self.log_service.warning(task.task_id, f"用例 {idx}/{len(testcases)} 跳过: {testcase_name}", extra={
                    "testcase_id": testcase_info.get('testcase_id'),
                    "testcase_name": testcase_name,
                    "testcase_result": "skipped"
                })

        # 发送套件结果总结
        summary = f"套件执行完成: {passed} 通过, {failed} 失败, {skipped} 跳过"
        logger.info(f"{summary}")
        await self.log_service.info(task.task_id, summary)

        # 更新套件统计信息到数据库
        await self.db_client.update_suite_statistics(
            task.task_id,
            success_count=passed,
            failed_count=failed,
            skipped_count=skipped
        )

        return TaskResult.PASSED if failed == 0 else TaskResult.FAILED

    async def _execute_test_plan(self, task: ExecutionTask) -> TaskResult:
        """执行测试计划（多个套件串行执行）"""
        # 从task config中获取套件ID列表
        target_ids = task.config.get("target_ids", [])
        targets = task.config.get("targets", [])

        if not target_ids:
            error_msg = "测试计划没有配置套件"
            await self.log_service.error(task.task_id, error_msg)
            raise ValueError(error_msg)

        logger.info(f"执行测试计划: {len(target_ids)} 个套件")
        await self.log_service.info(task.task_id, f"开始执行测试计划: {len(target_ids)} 个套件")

        passed_suites = 0
        failed_suites = 0

        for idx, suite_id in enumerate(target_ids, 1):
            # 获取套件名称
            suite_name = "Unknown"
            for target in targets:
                if target.get("id") == suite_id:
                    suite_name = target.get("name", "Unknown")
                    break

            logger.info(f"套件 {idx}/{len(target_ids)}: {suite_name}")
            await self.log_service.info(task.task_id, f"套件 {idx}/{len(target_ids)}: {suite_name}")

            # 创建套件任务
            suite_task = ExecutionTask(
                task_id=f"{task.task_id}_suite_{suite_id}",
                execution_type=ExecutionType.SUITE,
                target_id=suite_id,
                device_serial=task.device_serial,
                config=task.config
            )

            try:
                result = await self._execute_suite(suite_task)

                if result == TaskResult.PASSED:
                    passed_suites += 1
                    logger.info(f"套件通过: {suite_name}")
                    await self.log_service.info(task.task_id, f"套件 {idx}/{len(target_ids)} 通过: {suite_name}")
                else:
                    failed_suites += 1
                    logger.error(f"套件失败: {suite_name}")
                    await self.log_service.error(task.task_id, f"套件 {idx}/{len(target_ids)} 失败: {suite_name}")

            except Exception as e:
                failed_suites += 1
                error_msg = f"套件执行异常: {suite_name} - {str(e)}"
                logger.error(f"{error_msg}")
                await self.log_service.error(task.task_id, error_msg)

        # 发送测试计划总结
        summary = f"测试计划执行完成: {passed_suites} 通过, {failed_suites} 失败"
        logger.info(f"{summary}")
        await self.log_service.info(task.task_id, summary)

        # 更新测试计划统计信息到数据库
        await self.db_client.update_suite_statistics(
            task.task_id,
            success_count=passed_suites,
            failed_count=failed_suites,
            skipped_count=0
        )

        return TaskResult.PASSED if failed_suites == 0 else TaskResult.FAILED
