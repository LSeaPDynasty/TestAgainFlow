"""
Test Execution Engine Core
管理测试执行生命周期
"""
import asyncio
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import json

from .config import settings
from ..services.adb_service import ADBService
from ..services.db_client import DatabaseClient
from ..services.websocket_client import ExecutorWebSocketClient
from ..services.task_queue_client import TaskQueueClient
from ..drivers import create_driver
from .execution_queue import ExecutionQueue
from .task import ExecutionTask, TaskStatus, TaskResult
from ..utils.backend_log_handler import BackendLogHandler, set_current_task_id, clear_current_task_id

logger = logging.getLogger(__name__)


class ExecutionType(str):
    """执行类型"""
    STEP = "step"
    FLOW = "flow"
    TESTCASE = "testcase"
    SUITE = "suite"
    TEST_PLAN = "test_plan"


class TestExecutor:
    """
    主测试执行器
    管理执行队列并处理测试执行
    """

    def __init__(self, adb_service: ADBService, backend_ws_url: str = "ws://localhost:8000"):
        self.adb_service = adb_service
        self.db_client = DatabaseClient()
        self.execution_queue = ExecutionQueue(max_size=settings.max_concurrent_executions)
        self.active_tasks: Dict[str, ExecutionTask] = {}
        self.is_running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._poller_task: Optional[asyncio.Task] = None

        # WebSocket客户端连接到后端
        self.ws_client = ExecutorWebSocketClient(backend_ws_url)

        # 任务队列客户端
        self.task_queue_client = TaskQueueClient(backend_ws_url)

        # 设备自动发现
        from ..services.device_discovery import DeviceAutoDiscovery
        self.device_discovery = DeviceAutoDiscovery(self.ws_client)

        # 后端日志处理器（将在 start 中初始化）
        self.backend_log_handler: Optional[BackendLogHandler] = None

    async def start(self):
        """启动执行引擎"""
        if self.is_running:
            logger.warning("⚠️  执行引擎已在运行")
            return

        self.is_running = True

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

        # 添加到根 logger，这样所有模块的日志都会被捕获
        root_logger = logging.getLogger()
        root_logger.addHandler(self.backend_log_handler)

        # 发送启动状态
        await self.ws_client.send_status_update("running", {
            "concurrent": settings.max_concurrent_executions,
            "timeout": settings.execution_timeout
        })

        # 启动设备自动发现和注册
        self._discovery_task = asyncio.create_task(self.device_discovery.start_background_scan())

        # 启动工作线程
        self._worker_task = asyncio.create_task(self._worker())

        # 启动任务队列监听
        self._poller_task = asyncio.create_task(self._listen_task_queue())

        logger.info("✅ 执行引擎已启动")

    async def stop(self):
        """停止执行引擎"""
        if not self.is_running:
            return

        logger.info("🛑 停止执行引擎...")
        self.is_running = False

        # 发送停止状态
        await self.ws_client.send_status_update("stopped")

        # 取消任务
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        if self._poller_task:
            self._poller_task.cancel()
            try:
                await self._poller_task
            except asyncio.CancelledError:
                pass

        # 等待活动任务完成
        if self.active_tasks:
            logger.info(f"⏳ 等待 {len(self.active_tasks)} 个活动任务完成...")
            for task_id, task in list(self.active_tasks.items()):
                if task.status == TaskStatus.RUNNING:
                    logger.info(f"🚫 取消任务: {task_id}")
                    await task.cancel()

        # 关闭数据库连接
        await self.db_client.close()

        # 移除后端日志处理器
        if self.backend_log_handler:
            root_logger = logging.getLogger()
            root_logger.removeHandler(self.backend_log_handler)

        # 断开WebSocket连接
        await self.ws_client.disconnect()

        # 断开任务队列连接
        await self.task_queue_client.disconnect()

        logger.info("✅ 执行引擎已停止")

    def _create_driver_for_task(self, task: ExecutionTask):
        platform = (task.config or {}).get("platform", "android")
        return create_driver(platform, self.adb_service)

    async def _listen_task_queue(self):
        """从任务队列获取待执行任务"""
        logger.info("🔄 启动任务队列监听")

        while self.is_running:
            try:
                # 检查队列是否已满
                if self.execution_queue.full():
                    logger.debug("⏸️  执行队列已满，等待中...")
                    await asyncio.sleep(5)
                    continue

                # 从任务队列获取任务
                task_info = await self.task_queue_client.wait_for_task(timeout=10.0)

                if task_info:
                    task_id = task_info["task_id"]
                    task_data = task_info["task_data"]

                    try:
                        # 创建执行任务
                        task_config = dict(task_data.get("config") or {})
                        task_config.setdefault("platform", task_data.get("platform", "android"))

                        # For test_plan, store all target_ids in config
                        target_ids = task_data.get("target_ids", [])
                        if task_data.get("type") == "test_plan" and target_ids:
                            task_config["target_ids"] = target_ids
                            task_config["targets"] = task_data.get("targets", [])

                        task = ExecutionTask(
                            task_id=task_id,
                            execution_type=task_data.get("type", "testcase"),
                            target_id=target_ids[0] if target_ids else None,
                            device_serial=task_data.get("device_serial", ""),
                            config=task_config,
                        )

                        # 加入队列
                        await self.execution_queue.put(task)
                        self.active_tasks[task.task_id] = task

                        # 发送状态更新
                        await self.task_queue_client.send_task_status(task_id, "picked_up")

                        logger.info(
                            f"📝 任务入队: {task.task_id} "
                            f"({task_data.get('type')} #{task_data.get('target_ids', [])}) "
                            f"on {task_data.get('device_serial', 'unknown')}"
                        )

                    except Exception as e:
                        logger.error(f"❌ 任务入队失败: {e}", exc_info=True)
                        # 发送错误状态
                        await self.task_queue_client.send_task_status(task_id, "error", {"error": str(e)})

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 任务队列监听错误: {e}", exc_info=True)
                await asyncio.sleep(5)

        logger.info("🛑 任务队列监听已停止")

    async def _worker(self):
        """工作线程主循环，处理执行队列"""
        logger.info("🔄 启动工作线程")

        while self.is_running:
            try:
                # 从队列获取任务
                task = await asyncio.wait_for(
                    self.execution_queue.get(),
                    timeout=1.0
                )

                # 执行任务
                asyncio.create_task(self._execute_task(task))

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"❌ 工作线程错误: {e}", exc_info=True)
                await asyncio.sleep(1)

        logger.info("🛑 工作线程已停止")

    async def _execute_task(self, task: ExecutionTask):
        """执行单个任务"""
        task_id = task.task_id

        # 设置当前任务 ID，这样所有 logger 输出都会自动发送到后端
        set_current_task_id(task_id)

        logger.info(f"▶️  开始执行任务: {task_id}")

        # 发送任务开始更新
        await self.ws_client.send_task_update(task_id, {
            "status": "running",
            "run_type": task.execution_type,
            "target_id": task.target_id,
            "device_serial": task.device_serial
        })

        # 创建步骤执行器实例（用于收集截图）
        step_executor = None

        try:
            await task.start()

            # 更新数据库状态
            await self.db_client.update_execution_status(
                task_id=task_id,
                status="running"
            )

            # 根据类型执行
            if task.execution_type == ExecutionType.STEP:
                from .step_executor import StepExecutor
                step_executor = StepExecutor(self._create_driver_for_task(task), task)
                step_data = await self.db_client.get_step(task.target_id)
                result = await step_executor.execute_with_data(step_data)
            elif task.execution_type == ExecutionType.FLOW:
                result = await self._execute_flow(task)
            elif task.execution_type == ExecutionType.TESTCASE:
                result = await self._execute_testcase(task)
            elif task.execution_type == ExecutionType.SUITE:
                result = await self._execute_suite(task)
            elif task.execution_type == ExecutionType.TEST_PLAN:
                result = await self._execute_test_plan(task)
            else:
                raise ValueError(f"未知的执行类型: {task.execution_type}")

            await task.complete(result)

            # 收集失败截图
            failure_screenshots = []
            if step_executor:
                failure_screenshots = step_executor.get_failure_screenshots()

            # 更新数据库
            await self.db_client.update_execution_status(
                task_id=task_id,
                status="pass" if result == TaskResult.PASSED else "fail" if result == TaskResult.FAILED else "skipped",
                duration=task.duration
            )

            # 发送任务完成更新（包含截图信息）
            await self.ws_client.send_task_update(task_id, {
                "status": "completed" if result == TaskResult.PASSED else "failed" if result == TaskResult.FAILED else "skipped",
                "result": result.value,
                "duration": task.duration,
                "failure_screenshots": failure_screenshots
            })

            # 通过任务队列发送截图信息到后端
            if failure_screenshots:
                await self.task_queue_client.send_message("task_screenshots", {
                    "task_id": task_id,
                    "screenshots": failure_screenshots
                })

            await self.ws_client.send_log("INFO", f"任务完成: {task_id} -> {result.value}", "executor")
            await self.task_queue_client.send_task_status(
                task_id,
                "completed" if result != TaskResult.FAILED else "failed",
                {
                    "result": result.value,
                    "duration": task.duration,
                },
            )

            logger.info(f"✅ 任务完成: {task_id} -> {result.value}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ 任务失败: {task_id} - {error_msg}", exc_info=True)

            await task.fail(error_msg)

            # 更新数据库
            await self.db_client.update_execution_status(
                task_id=task_id,
                status="error"
            )

            # 发送任务失败更新
            await self.ws_client.send_task_update(task_id, {
                "status": "failed",
                "error": error_msg
            })

            await self.ws_client.send_log("ERROR", f"任务失败: {task_id} - {error_msg}", "executor")
            await self.task_queue_client.send_task_status(
                task_id,
                "failed",
                {"error": error_msg},
            )

        finally:
            # 清除当前任务 ID
            clear_current_task_id()

            # 清理
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    async def _execute_step(self, task: ExecutionTask) -> TaskResult:
        """执行单个步骤"""
        # 从数据库获取步骤详情
        step_data = await self.db_client.get_step(task.target_id)
        return await self._execute_step_with_data(task, step_data)

    async def _execute_step_with_data(self, task: ExecutionTask, step_data: Dict[str, Any]) -> TaskResult:
        """执行单个步骤（使用预加载的步骤数据）"""
        from .step_executor import StepExecutor

        if not step_data:
            raise ValueError(f"步骤数据为空")

        step_executor = StepExecutor(self._create_driver_for_task(task), task)
        return await step_executor.execute_with_data(step_data)

    async def _execute_flow(self, task: ExecutionTask) -> TaskResult:
        """执行流程（多个步骤）"""
        # 从数据库获取流程详情
        flow_data = await self.db_client.get_flow(task.target_id)

        if not flow_data:
            error_msg = f"流程不存在: {task.target_id}"
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "ERROR",
                "message": error_msg,
                "timestamp": asyncio.get_event_loop().time()
            })
            raise ValueError(error_msg)

        flow_type = flow_data.get("flow_type", "standard")

        task.log(f"📋 执行流程: {flow_data.get('name', 'Unknown')}")
        task.log(f"   类型: {flow_type}")
        task.log(f"   步骤数: {len(flow_data.get('steps', []))}")

        # 发送流程开始日志
        await self.task_queue_client.send_task_log(task.task_id, {
            "level": "INFO",
            "message": f"执行流程: {flow_data.get('name', 'Unknown')} ({flow_type}, {len(flow_data.get('steps', []))} 步)",
            "timestamp": asyncio.get_event_loop().time()
        })

        try:
            if flow_type == "dsl":
                # 执行DSL流程
                return await self._execute_dsl_flow(task, flow_data)
            elif flow_type == "python":
                # 执行Python流程
                return await self._execute_python_flow(task, flow_data)
            else:
                # 执行标准流程
                return await self._execute_standard_flow(task, flow_data)
        except Exception as e:
            error_msg = f"流程执行异常: {str(e)}"
            task.log(f"❌ {error_msg}")
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "ERROR",
                "message": error_msg,
                "timestamp": asyncio.get_event_loop().time()
            })
            return TaskResult.FAILED

    async def _execute_standard_flow(self, task: ExecutionTask, flow_data: Dict) -> TaskResult:
        """执行标准流程"""
        from .step_executor import StepExecutor

        steps = flow_data.get("steps", [])

        await self.task_queue_client.send_task_log(task.task_id, {
            "level": "INFO",
            "message": f"开始执行标准流程，共 {len(steps)} 个步骤",
            "timestamp": asyncio.get_event_loop().time()
        })

        for idx, step_data in enumerate(steps, 1):
            step_name = step_data.get("name", "Unknown")
            action_type = step_data.get("action_type", "Unknown")
            screen_name = step_data.get("screen_name", "Unknown")
            element_name = step_data.get("element_name", "")

            task.log(f"\n📍 步骤 {idx}/{len(steps)}: {step_name}")
            task.log(f"   动作: {action_type}")
            task.log(f"   屏幕: {screen_name}")
            task.log(f"   元素: {element_name}")

            # 发送步骤开始日志
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "INFO",
                "message": f"步骤 {idx}/{len(steps)}: {action_type} - {step_name} (屏幕: {screen_name}, 元素: {element_name})",
                "timestamp": asyncio.get_event_loop().time()
            })

            try:
                step_executor = StepExecutor(self._create_driver_for_task(task), task)

                # 执行步骤前发送开始日志
                await self.task_queue_client.send_task_log(task.task_id, {
                    "level": "INFO",
                    "message": f"步骤 {idx}/{len(steps)}: {step_name} ({action_type})",
                    "timestamp": asyncio.get_event_loop().time()
                })

                result = await step_executor.execute_with_data(step_data)

                if result == TaskResult.FAILED:
                    # 检查是否设置了失败后继续执行
                    continue_on_error = step_data.get("continue_on_error", 0)

                    if continue_on_error:
                        # 失败但继续执行
                        error_msg = f"流程在步骤 {idx} 失败（继续执行）: {step_name} - {action_type}"
                        task.log(f"⚠️ {error_msg}")
                        await self.task_queue_client.send_task_log(task.task_id, {
                            "level": "WARNING",
                            "message": f"[步骤 {idx}/{len(steps)}] 执行失败（继续执行）: {step_name}",
                            "timestamp": asyncio.get_event_loop().time()
                        })
                        # 不返回，继续执行下一个步骤
                    else:
                        # 失败且停止执行
                        error_msg = f"流程在步骤 {idx} 失败: {step_name} - {action_type}"
                        task.log(f"❌ {error_msg}")
                        await self.task_queue_client.send_task_log(task.task_id, {
                            "level": "ERROR",
                            "message": f"[步骤 {idx}/{len(steps)}] 执行失败: {step_name}",
                            "timestamp": asyncio.get_event_loop().time()
                        })
                        return TaskResult.FAILED

                if result == TaskResult.SKIPPED:
                    skip_msg = f"流程在步骤 {idx} 跳过: {step_name}"
                    task.log(f"⏭️  {skip_msg}")
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "WARNING",
                        "message": f"[步骤 {idx}/{len(steps)}] 跳过: {step_name}",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    return TaskResult.SKIPPED

                # 步骤成功
                await self.task_queue_client.send_task_log(task.task_id, {
                    "level": "SUCCESS",
                    "message": f"[步骤 {idx}/{len(steps)}] 执行成功: {step_name}",
                    "timestamp": asyncio.get_event_loop().time()
                })

            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                error_msg = f"步骤 {idx} 执行异常: {step_name} - {str(e)}"
                task.log(f"❌ {error_msg}")
                task.log(f"   详细错误:\n{error_detail}")

                # 检查是否设置了失败后继续执行
                continue_on_error = step_data.get("continue_on_error", 0)

                if continue_on_error:
                    # 异常但继续执行
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "WARNING",
                        "message": f"[步骤 {idx}/{len(steps)}] 执行异常（继续执行）: {step_name} - {str(e)}",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    # 发送完整的堆栈跟踪
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "WARNING",
                        "message": f"异常堆栈:\n{error_detail}",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    # 不返回，继续执行下一个步骤
                else:
                    # 异常且停止执行
                    # 发送详细的错误信息
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "ERROR",
                        "message": f"[步骤 {idx}/{len(steps)}] 执行异常: {step_name} - {str(e)}",
                        "timestamp": asyncio.get_event_loop().time()
                    })

                    # 发送完整的堆栈跟踪
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "ERROR",
                        "message": f"异常堆栈:\n{error_detail}",
                        "timestamp": asyncio.get_event_loop().time()
                    })

                    return TaskResult.FAILED

        task.log(f"\n✅ 流程执行成功")
        await self.task_queue_client.send_task_log(task.task_id, {
            "level": "INFO",
            "message": "流程执行成功",
            "timestamp": asyncio.get_event_loop().time()
        })

        return TaskResult.PASSED

    async def _execute_dsl_flow(self, task: ExecutionTask, flow_data: Dict) -> TaskResult:
        """执行DSL流程"""
        dsl_content = flow_data.get("dsl_content", "")

        if not dsl_content:
            raise ValueError("DSL流程没有内容")

        task.log("🔧 执行DSL流程...")
        task.log("⚠️  DSL执行尚未实现")
        return TaskResult.SKIPPED

    async def _execute_python_flow(self, task: ExecutionTask, flow_data: Dict) -> TaskResult:
        """执行Python流程"""
        python_content = flow_data.get("python_content", "")

        if not python_content:
            raise ValueError("Python流程没有内容")

        task.log("🐍 执行Python流程...")
        task.log("⚠️  Python执行尚未实现")
        return TaskResult.SKIPPED

    async def _execute_testcase_items(self, task: ExecutionTask, testcase_items: List[Dict]) -> TaskResult:
        """
        执行testcase_items（支持flow/step混排）

        Args:
            task: 执行任务
            testcase_items: testcase_items列表，包含item_type, flow_id, step_id, enabled, continue_on_error等

        Returns:
            TaskResult: 执行结果
        """
        task.log(f"\n▶️  Main阶段 ({len(testcase_items)} 个items, 支持flow/step混排)")
        await self.task_queue_client.send_task_log(task.task_id, {
            "level": "INFO",
            "message": f"Main阶段: {len(testcase_items)} 个items (flow/step混排)",
            "timestamp": asyncio.get_event_loop().time()
        })

        # ✅ 批量预加载所有步骤数据 - 解决N+1查询问题
        step_ids = [item.get("step_id") for item in testcase_items if item.get("item_type") == "step"]
        steps_map = await self.db_client.get_steps_batch(step_ids) if step_ids else {}

        final_result = TaskResult.PASSED
        enabled_count = 0

        for idx, item in enumerate(testcase_items, 1):
            # 检查是否启用
            if not item.get("enabled", 1):
                continue

            enabled_count += 1
            item_type = item.get("item_type")
            item_id = item.get("id")
            continue_on_error = item.get("continue_on_error", False)

            if item_type == "flow":
                flow_id = item.get("flow_id")
                flow_name = item.get("flow_name", f"Flow-{flow_id}")

                task.log(f"\n📍 Item {enabled_count}/{len(testcase_items)}: [Flow] {flow_name}")
                await self.task_queue_client.send_task_log(task.task_id, {
                    "level": "INFO",
                    "message": f"Item {enabled_count}: Flow - {flow_name}",
                    "timestamp": asyncio.get_event_loop().time()
                })

                # 创建并执行flow任务
                flow_task = ExecutionTask(
                    task_id=f"{task.task_id}_item_{item_id}",
                    execution_type=ExecutionType.FLOW,
                    target_id=flow_id,
                    device_serial=task.device_serial,
                    config=task.config
                )

                result = await self._execute_flow(flow_task)

                if result != TaskResult.PASSED:
                    error_msg = f"Flow执行失败: {flow_name}"
                    task.log(f"❌ {error_msg}")
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "ERROR",
                        "message": error_msg,
                        "timestamp": asyncio.get_event_loop().time()
                    })

                    if not continue_on_error:
                        final_result = TaskResult.FAILED
                        break
                    else:
                        task.log(f"⚠️  但continue_on_error=True，继续执行")
                        await self.task_queue_client.send_task_log(task.task_id, {
                            "level": "WARNING",
                            "message": f"Flow失败但继续执行: {flow_name}",
                            "timestamp": asyncio.get_event_loop().time()
                        })

            elif item_type == "step":
                step_id = item.get("step_id")
                step_name = item.get("step_name", f"Step-{step_id}")
                step_action_type = item.get("step_action_type", "unknown")

                task.log(f"\n📍 Item {enabled_count}/{len(testcase_items)}: [Step] {step_name} ({step_action_type})")
                await self.task_queue_client.send_task_log(task.task_id, {
                    "level": "INFO",
                    "message": f"Item {enabled_count}: Step - {step_name} ({step_action_type})",
                    "timestamp": asyncio.get_event_loop().time()
                })

                # ✅ 使用预加载的步骤数据，避免重复查询
                step_data = steps_map.get(step_id)
                if not step_data:
                    error_msg = f"步骤数据不存在: {step_id}"
                    task.log(f"❌ {error_msg}")
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "ERROR",
                        "message": error_msg,
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    final_result = TaskResult.FAILED
                    break

                # 创建并执行step任务（传入预加载的step_data）
                step_task = ExecutionTask(
                    task_id=f"{task.task_id}_item_{item_id}",
                    execution_type=ExecutionType.STEP,
                    target_id=step_id,
                    device_serial=task.device_serial,
                    config={**task.config, "step_data": step_data}  # ✅ 传递预加载的数据
                )

                result = await self._execute_step_with_data(step_task, step_data)

                if result != TaskResult.PASSED:
                    error_msg = f"Step执行失败: {step_name}"
                    task.log(f"❌ {error_msg}")
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "ERROR",
                        "message": error_msg,
                        "timestamp": asyncio.get_event_loop().time()
                    })

                    if not continue_on_error:
                        final_result = TaskResult.FAILED
                        break
                    else:
                        task.log(f"⚠️  但continue_on_error=True，继续执行")
                        await self.task_queue_client.send_task_log(task.task_id, {
                            "level": "WARNING",
                            "message": f"Step失败但继续执行: {step_name}",
                            "timestamp": asyncio.get_event_loop().time()
                        })
            else:
                error_msg = f"未知的item_type: {item_type}"
                task.log(f"❌ {error_msg}")
                await self.task_queue_client.send_task_log(task.task_id, {
                    "level": "ERROR",
                    "message": error_msg,
                    "timestamp": asyncio.get_event_loop().time()
                })
                final_result = TaskResult.FAILED
                break

        return final_result

    async def _execute_testcase(self, task: ExecutionTask) -> TaskResult:
        """执行用例（setup + main/teardown）"""
        testcase_data = await self.db_client.get_testcase(task.target_id)

        if not testcase_data:
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "ERROR",
                "message": f"用例不存在: {task.target_id}",
                "timestamp": asyncio.get_event_loop().time()
            })
            raise ValueError(f"用例不存在: {task.target_id}")

        task.log(f"📝 执行用例: {testcase_data.get('name', 'Unknown')}")

        # 发送日志到后端
        await self.task_queue_client.send_task_log(task.task_id, {
            "level": "INFO",
            "message": f"开始执行用例: {testcase_data.get('name', 'Unknown')}",
            "timestamp": asyncio.get_event_loop().time()
        })

        # 标记最终结果
        final_result = TaskResult.PASSED

        # 执行setup流程
        setup_flows = testcase_data.get("setup_flows", [])
        if setup_flows:
            task.log(f"\n🔧 Setup阶段 ({len(setup_flows)} 个流程)")
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "INFO",
                "message": f"Setup阶段: {len(setup_flows)} 个流程",
                "timestamp": asyncio.get_event_loop().time()
            })

            for flow_info in setup_flows:
                if not flow_info.get("enabled", 1):
                    continue

                flow_task = ExecutionTask(
                    task_id=f"{task.task_id}_setup_{flow_info['id']}",
                    execution_type=ExecutionType.FLOW,
                    target_id=flow_info["flow_id"],
                    device_serial=task.device_serial,
                    config=task.config
                )

                result = await self._execute_flow(flow_task)
                if result != TaskResult.PASSED:
                    error_msg = f"Setup失败: {flow_info.get('name', flow_info['id'])}"
                    task.log(f"❌ {error_msg}")
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "ERROR",
                        "message": error_msg,
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    return TaskResult.FAILED

        # 执行main阶段：优先使用testcase_items，否则使用main_flows（向后兼容）
        testcase_items = testcase_data.get("testcase_items", [])
        if testcase_items:
            # 新格式：执行testcase_items（支持flow/step混排）
            main_result = await self._execute_testcase_items(task, testcase_items)
            if main_result != TaskResult.PASSED:
                final_result = main_result
        else:
            # 旧格式：执行main_flows（向后兼容）
            main_flows = testcase_data.get("main_flows", [])
            if main_flows:
                task.log(f"\n▶️  Main阶段 ({len(main_flows)} 个流程)")
                await self.task_queue_client.send_task_log(task.task_id, {
                    "level": "INFO",
                    "message": f"Main阶段: {len(main_flows)} 个流程",
                    "timestamp": asyncio.get_event_loop().time()
                })

                for flow_info in main_flows:
                    if not flow_info.get("enabled", 1):
                        continue

                    flow_task = ExecutionTask(
                        task_id=f"{task.task_id}_main_{flow_info['id']}",
                        execution_type=ExecutionType.FLOW,
                        target_id=flow_info["flow_id"],
                        device_serial=task.device_serial,
                        config=task.config
                    )

                    result = await self._execute_flow(flow_task)
                    if result != TaskResult.PASSED:
                        error_msg = f"Main失败: {flow_info.get('name', flow_info['id'])}"
                        task.log(f"❌ {error_msg}")
                        await self.task_queue_client.send_task_log(task.task_id, {
                            "level": "ERROR",
                            "message": error_msg,
                            "timestamp": asyncio.get_event_loop().time()
                        })
                        final_result = TaskResult.FAILED
                        break  # Main失败后跳出循环，但仍要执行teardown

        # 执行teardown流程（总是执行，即使main失败）
        teardown_flows = testcase_data.get("teardown_flows", [])
        if teardown_flows:
            task.log(f"\n🧹 Teardown阶段 ({len(teardown_flows)} 个流程)")
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "INFO",
                "message": f"Teardown阶段: {len(teardown_flows)} 个流程",
                "timestamp": asyncio.get_event_loop().time()
            })

            for flow_info in teardown_flows:
                if not flow_info.get("enabled", 1):
                    continue

                flow_task = ExecutionTask(
                    task_id=f"{task.task_id}_teardown_{flow_info['id']}",
                    execution_type=ExecutionType.FLOW,
                    target_id=flow_info["flow_id"],
                    device_serial=task.device_serial,
                    config=task.config
                )

                result = await self._execute_flow(flow_task)
                # Teardown失败不影响用例结果，但记录日志
                if result != TaskResult.PASSED:
                    task.log(f"⚠️  Teardown警告: {flow_info.get('name', flow_info['id'])} 执行失败")
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "WARNING",
                        "message": f"Teardown失败: {flow_info.get('name', flow_info['id'])}",
                        "timestamp": asyncio.get_event_loop().time()
                    })

        # 根据最终结果返回
        if final_result == TaskResult.PASSED:
            task.log(f"\n✅ 用例执行成功")
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "INFO",
                "message": "用例执行成功",
                "timestamp": asyncio.get_event_loop().time()
            })
        else:
            task.log(f"\n❌ 用例执行失败")
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "ERROR",
                "message": "用例执行失败",
                "timestamp": asyncio.get_event_loop().time()
            })

        return final_result

    async def _execute_suite(self, task: ExecutionTask) -> TaskResult:
        """执行套件（多个用例）"""
        suite_data = await self.db_client.get_suite(task.target_id)

        if not suite_data:
            error_msg = f"套件不存在: {task.target_id}"
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "ERROR",
                "message": error_msg,
                "timestamp": asyncio.get_event_loop().time()
            })
            raise ValueError(error_msg)

        suite_name = suite_data.get('name', 'Unknown')
        testcases = suite_data.get("testcases", [])

        logger.info(f"📦 执行套件: {suite_name} ({len(testcases)} 个用例)")

        # 发送套件开始日志
        await self.task_queue_client.send_task_log(task.task_id, {
            "level": "INFO",
            "message": f"开始执行套件: {suite_name} ({len(testcases)} 个用例)",
            "timestamp": asyncio.get_event_loop().time()
        })

        passed = 0
        failed = 0
        skipped = 0

        for idx, testcase_info in enumerate(testcases, 1):
            if not testcase_info.get("enabled", 1):
                logger.info(f"⏭️  用例 {idx}/{len(testcases)}: 跳过（已禁用）")
                await self.task_queue_client.send_task_log(task.task_id, {
                    "level": "WARNING",
                    "message": f"用例 {idx}/{len(testcases)} 跳过（已禁用）: {testcase_info.get('name', 'Unknown')}",
                    "timestamp": asyncio.get_event_loop().time()
                })
                skipped += 1
                continue

            testcase_name = testcase_info.get('name', 'Unknown')
            logger.info(f"📝 用例 {idx}/{len(testcases)}: {testcase_name}")

            # 发送用例开始日志（包含用例ID，便于前端聚合）
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "INFO",
                "message": f"用例 {idx}/{len(testcases)}: {testcase_name}",
                "testcase_id": testcase_info.get('testcase_id'),
                "testcase_name": testcase_name,
                "testcase_index": idx,
                "testcase_total": len(testcases),
                "timestamp": asyncio.get_event_loop().time()
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
                logger.info(f"✅ 用例通过: {testcase_name}")
                await self.task_queue_client.send_task_log(task.task_id, {
                    "level": "INFO",
                    "message": f"用例 {idx}/{len(testcases)} 通过: {testcase_name}",
                    "testcase_id": testcase_info.get('testcase_id'),
                    "testcase_name": testcase_name,
                    "testcase_result": "passed",
                    "timestamp": asyncio.get_event_loop().time()
                })
            elif result == TaskResult.FAILED:
                failed += 1
                logger.error(f"❌ 用例失败: {testcase_name}")
                await self.task_queue_client.send_task_log(task.task_id, {
                    "level": "ERROR",
                    "message": f"用例 {idx}/{len(testcases)} 失败: {testcase_name}",
                    "testcase_id": testcase_info.get('testcase_id'),
                    "testcase_name": testcase_name,
                    "testcase_result": "failed",
                    "timestamp": asyncio.get_event_loop().time()
                })
            else:
                skipped += 1
                logger.warning(f"⏭️  用例跳过: {testcase_name}")
                await self.task_queue_client.send_task_log(task.task_id, {
                    "level": "WARNING",
                    "message": f"用例 {idx}/{len(testcases)} 跳过: {testcase_name}",
                    "testcase_id": testcase_info.get('testcase_id'),
                    "testcase_name": testcase_name,
                    "testcase_result": "skipped",
                    "timestamp": asyncio.get_event_loop().time()
                })

        # 发送套件结果总结
        summary = f"套件执行完成: {passed} 通过, {failed} 失败, {skipped} 跳过"
        logger.info(f"📊 {summary}")
        await self.task_queue_client.send_task_log(task.task_id, {
            "level": "INFO",
            "message": summary,
            "timestamp": asyncio.get_event_loop().time()
        })

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
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "ERROR",
                "message": error_msg,
                "timestamp": asyncio.get_event_loop().time()
            })
            raise ValueError(error_msg)

        task.log(f"📋 执行测试计划: {len(target_ids)} 个套件")

        # 发送测试计划开始日志
        await self.task_queue_client.send_task_log(task.task_id, {
            "level": "INFO",
            "message": f"开始执行测试计划: {len(target_ids)} 个套件",
            "timestamp": asyncio.get_event_loop().time()
        })

        passed_suites = 0
        failed_suites = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0

        for idx, suite_id in enumerate(target_ids, 1):
            # 获取套件名称
            suite_name = "Unknown"
            for target in targets:
                if target.get("id") == suite_id:
                    suite_name = target.get("name", "Unknown")
                    break

            task.log(f"\n📦 套件 {idx}/{len(target_ids)}: {suite_name}")
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "INFO",
                "message": f"套件 {idx}/{len(target_ids)}: {suite_name}",
                "timestamp": asyncio.get_event_loop().time()
            })

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

                # 从suite_task的日志中获取统计信息
                # 由于_execute_suite会更新数据库，我们可以从数据库读取
                # 或者简单计数通过/失败的套件数

                if result == TaskResult.PASSED:
                    passed_suites += 1
                    task.log(f"✅ 套件通过: {suite_name}")
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "SUCCESS",
                        "message": f"套件 {idx}/{len(target_ids)} 通过: {suite_name}",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                else:
                    failed_suites += 1
                    task.log(f"❌ 套件失败: {suite_name}")
                    await self.task_queue_client.send_task_log(task.task_id, {
                        "level": "ERROR",
                        "message": f"套件 {idx}/{len(target_ids)} 失败: {suite_name}",
                        "timestamp": asyncio.get_event_loop().time()
                    })

            except Exception as e:
                failed_suites += 1
                error_msg = f"套件执行异常: {suite_name} - {str(e)}"
                task.log(f"❌ {error_msg}")
                await self.task_queue_client.send_task_log(task.task_id, {
                    "level": "ERROR",
                    "message": error_msg,
                    "timestamp": asyncio.get_event_loop().time()
                })

        # 发送测试计划总结
        summary = f"测试计划执行完成: {passed_suites} 通过, {failed_suites} 失败"
        task.log(f"\n📊 {summary}")
        await self.task_queue_client.send_task_log(task.task_id, {
            "level": "INFO",
            "message": summary,
            "timestamp": asyncio.get_event_loop().time()
        })

        # 更新测试计划统计信息到数据库
        await self.db_client.update_suite_statistics(
            task.task_id,
            success_count=passed_suites,
            failed_count=failed_suites,
            skipped_count=0
        )

        return TaskResult.PASSED if failed_suites == 0 else TaskResult.FAILED
