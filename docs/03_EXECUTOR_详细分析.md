# TestFlow Executor - 测试执行引擎详细分析

## 项目概述

TestFlow Executor 是一个独立的测试执行引擎应用程序，负责执行 Android 自动化测试任务。它不提供 Web 服务，而是通过数据库轮询和 WebSocket 与后端通信，实现任务获取和状态更新。

### 基本信息
- **架构**: 独立应用程序（非Web服务）
- **语言**: Python 3.9+
- **通信方式**: 数据库轮询 + WebSocket推送
- **并发模型**: asyncio 异步I/O
- **设备控制**: ADB (Android Debug Bridge)

---

## 核心架构

### 系统定位

```
┌─────────────────────────────────────────────────────────┐
│                    TestFlow 平台                         │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐      ┌──────────────┐                │
│  │   Frontend   │      │   Backend    │                │
│  │   (React)    │ ←──→ │   (FastAPI)  │                │
│  │  Port: 3002  │      │  Port: 8000  │                │
│  └──────────────┘      └──────┬───────┘                │
│                                ↓                         │
│                        ┌───────────────┐                │
│                        │   Database    │                │
│                        │  (SQLite)     │                │
│                        └───────┬───────┘                │
│                                ↓                         │
│                    ┌───────────────────────┐            │
│                    │    TestFlow           │            │
│                    │    Executor           │            │
│                    │  (独立应用)           │            │
│                    └───────────────────────┘            │
│                                ↓                         │
│                        ┌───────────────┐                │
│                        │   Devices    │                │
│                        │  (Android)   │                │
│                        └───────────────┘                │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 数据流设计

```
1. 任务创建
   前端 → Backend API → Database (runs表, status=pending)

2. 任务获取
   Executor 轮询 Database → SELECT pending tasks

3. 任务执行
   Executor → ADB → Android Device

4. 状态更新
   Executor → Database (UPDATE runs.status)
   Executor → WebSocket → Backend → Frontend (实时推送)

5. 日志流式传输
   Executor → WebSocket → Backend → Frontend (实时日志)
```

---

## 核心模块详解

### 1. 执行器核心 (TestExecutor)

#### 类结构
```python
class TestExecutor:
    """主测试执行器 - 管理执行队列并处理测试执行"""

    def __init__(self, adb_service: ADBService, backend_ws_url: str):
        # 服务依赖
        self.adb_service = adb_service
        self.db_client = DatabaseClient()

        # 队列管理
        self.execution_queue = ExecutionQueue(
            max_size=settings.max_concurrent_executions
        )
        self.active_tasks: Dict[str, ExecutionTask] = {}

        # 通信客户端
        self.ws_client = ExecutorWebSocketClient(backend_ws_url)
        self.task_queue_client = TaskQueueClient(backend_ws_url)

        # 设备自动发现
        self.device_discovery = DeviceAutoDiscovery(self.ws_client)

        # 日志处理
        self.backend_log_handler = BackendLogHandler(
            self.task_queue_client
        )
```

#### 生命周期管理

**启动流程**:
```python
async def start(self):
    """启动执行引擎"""
    # 1. 连接数据库
    await self.db_client.connect()

    # 2. 连接WebSocket
    await self.ws_client.connect()
    await self.task_queue_client.connect()

    # 3. 初始化日志处理器
    self.backend_log_handler = BackendLogHandler(...)
    logging.getLogger().addHandler(self.backend_log_handler)

    # 4. 发送启动状态
    await self.ws_client.send_status_update("running", {
        "concurrent": settings.max_concurrent_executions,
        "timeout": settings.execution_timeout
    })

    # 5. 启动设备自动发现
    self._discovery_task = asyncio.create_task(
        self.device_discovery.start_background_scan()
    )

    # 6. 启动工作线程
    self._worker_task = asyncio.create_task(self._worker())

    # 7. 启动任务队列监听
    self._poller_task = asyncio.create_task(self._listen_task_queue())

    logger.info("✅ 执行引擎已启动")
```

**停止流程**:
```python
async def stop(self):
    """停止执行引擎"""
    # 1. 发送停止状态
    await self.ws_client.send_status_update("stopped")

    # 2. 取消后台任务
    self._worker_task.cancel()
    self._poller_task.cancel()
    self._discovery_task.cancel()

    # 3. 等待活动任务完成
    for task_id, task in self.active_tasks.items():
        if task.status == TaskStatus.RUNNING:
            await task.cancel()

    # 4. 清理资源
    await self.db_client.close()
    logging.getLogger().removeHandler(self.backend_log_handler)
    await self.ws_client.disconnect()

    logger.info("✅ 执行引擎已停止")
```

---

### 2. 执行队列 (ExecutionQueue)

#### 队列设计
```python
class ExecutionQueue:
    """异步执行队列 - 支持并发控制和优先级"""

    def __init__(self, max_size: int = 5):
        self.max_size = max_size
        self.queue: asyncio.Queue[ExecutionTask] = asyncio.Queue()
        self.active_tasks: Set[str] = set()
        self._semaphore = asyncio.Semaphore(max_size)

    async def put(self, task: ExecutionTask):
        """添加任务到队列"""
        await self.queue.put(task)

    async def get(self) -> ExecutionTask:
        """从队列获取任务（阻塞直到有可用槽位）"""
        await self._semaphore.acquire()  # 等待可用槽位
        task = await self.queue.get()
        self.active_tasks.add(task.id)
        return task

    def task_done(self, task_id: str):
        """标记任务完成，释放槽位"""
        self.active_tasks.discard(task_id)
        self._semaphore.release()
        self.queue.task_done()
```

#### 并发控制
```
┌─────────────────────────────────────┐
│         ExecutionQueue              │
│  ┌───────────────────────────────┐  │
│  │  Semaphore (max=5)            │  │
│  │  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐│  │
│  │  │ 1 │ │ 2 │ │ 3 │ │ 4 │ │ 5 ││  │
│  │  └───┘ └───┘ └───┘ └───┘ └───┘│  │
│  └───────────────────────────────┘  │
│                                     │
│  Waiting Queue:                     │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐          │
│  │ 6 │ │ 7 │ │ 8 │ │ 9 │ ...      │
│  └───┘ └───┘ └───┘ └───┘          │
└─────────────────────────────────────┘
```

---

### 3. 任务模型 (ExecutionTask)

#### 任务状态机
```
┌──────────┐
│  PENDING │  ← 初始状态
└────┬─────┘
     ↓
┌──────────┐
│ RUNNING  │  ← 执行中
└────┬─────┘
     ↓
┌──────────┐
│ PASSED   │  ← 成功
└──────────┘

     ↓ (失败)
┌──────────┐
│ FAILED   │  ← 失败
└──────────┘

     ↓ (取消)
┌──────────┐
│ CANCELLED│  ← 已取消
└──────────┘
```

#### 任务数据结构
```python
@dataclass
class ExecutionTask:
    """执行任务模型"""
    id: str
    execution_type: ExecutionType  # STEP/FLOW/TESTCASE/SUITE
    target_id: int
    device_serial: str
    priority: int = 1
    timeout: int = 3600
    retry_count: int = 0
    max_retries: int = 3

    # 执行状态
    status: TaskStatus = TaskStatus.PENDING
    result: TaskResult = TaskResult.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # 执行日志
    logs: List[Dict] = field(default_factory=list)

    async def execute(self, executor: TestExecutor):
        """执行任务"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

        try:
            # 获取设备驱动
            driver = create_driver(
                platform="android",
                device_serial=self.device_serial
            )

            # 根据类型执行
            if self.execution_type == ExecutionType.STEP:
                result = await self._execute_step(executor, driver)
            elif self.execution_type == ExecutionType.FLOW:
                result = await self._execute_flow(executor, driver)
            elif self.execution_type == ExecutionType.TESTCASE:
                result = await self._execute_testcase(executor, driver)
            elif self.execution_type == ExecutionType.SUITE:
                result = await self._execute_suite(executor, driver)

            self.result = result

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            self.result = TaskResult.FAILED
            self.logs.append({
                "level": "ERROR",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })

        finally:
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.now()

    async def cancel(self):
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.completed_at = datetime.now()
```

---

### 4. 步骤执行器 (StepExecutor)

#### 执行引擎
```python
class StepExecutor:
    """步骤执行器 - 执行单个测试步骤"""

    def __init__(self, adb_service: ADBService):
        self.adb_service = adb_service

    async def execute(
        self,
        step_data: Dict,
        driver: AndroidDriver
    ) -> TaskResult:
        """执行步骤"""
        action_type = step_data.get("action_type")

        # 根据操作类型分发
        if action_type == "click":
            return await self._execute_click(step_data, driver)
        elif action_type == "input":
            return await self._execute_input(step_data, driver)
        elif action_type == "swipe":
            return await self._execute_swipe(step_data, driver)
        elif action_type == "wait_element":
            return await self._execute_wait_element(step_data, driver)
        elif action_type == "wait_time":
            return await self._execute_wait_time(step_data)
        elif action_type.startswith("assert_"):
            return await self._execute_assert(step_data, driver)
        else:
            return await self._execute_custom(step_data, driver)
```

#### 操作实现

**点击操作**:
```python
async def _execute_click(
    self,
    step_data: Dict,
    driver: AndroidDriver
) -> TaskResult:
    """执行点击操作"""
    element = step_data.get("element")
    locators = element.get("locators", [])

    # 查找元素
    element_info = await self._find_element(driver, locators)
    if not element_info:
        logger.error(f"元素未找到: {element.get('name')}")
        return TaskResult.FAILED

    # 执行点击
    await driver.click(element_info)

    # 等待
    wait_after = step_data.get("wait_after_ms", 0)
    if wait_after > 0:
        await asyncio.sleep(wait_after / 1000)

    logger.info(f"✅ 点击成功: {element.get('name')}")
    return TaskResult.PASSED
```

**输入操作**:
```python
async def _execute_input(
    self,
    step_data: Dict,
    driver: AndroidDriver
) -> TaskResult:
    """执行输入操作"""
    element = step_data.get("element")
    value = step_data.get("action_value", "")
    locators = element.get("locators", [])

    # 查找元素
    element_info = await self._find_element(driver, locators)
    if not element_info:
        return TaskResult.FAILED

    # 清空并输入
    await driver.clear(element_info)
    await driver.input_text(element_info, value)

    logger.info(f"✅ 输入成功: {value}")
    return TaskResult.PASSED
```

**滑动操作**:
```python
async def _execute_swipe(
    self,
    step_data: Dict,
    driver: AndroidDriver
) -> TaskResult:
    """执行滑动操作"""
    direction = step_data.get("direction", "up")
    duration = step_data.get("duration", 500)
    percent = step_data.get("percent", 0.5)

    await driver.swipe(
        direction=direction,
        duration=duration,
        percent=percent
    )

    logger.info(f"✅ 滑动成功: {direction}")
    return TaskResult.PASSED
```

**等待元素**:
```python
async def _execute_wait_element(
    self,
    step_data: Dict,
    driver: AndroidDriver
) -> TaskResult:
    """等待元素出现"""
    element = step_data.get("element")
    timeout = step_data.get("timeout", 30)
    locators = element.get("locators", [])

    # 轮询查找
    for i in range(timeout * 10):  # 100ms间隔
        element_info = await self._find_element(driver, locators)
        if element_info:
            logger.info(f"✅ 元素已出现: {element.get('name')}")
            return TaskResult.PASSED
        await asyncio.sleep(0.1)

    logger.error(f"❌ 元素未出现: {element.get('name')}")
    return TaskResult.FAILED
```

**断言操作**:
```python
async def _execute_assert(
    self,
    step_data: Dict,
    driver: AndroidDriver
) -> TaskResult:
    """执行断言操作"""
    action_type = step_data.get("action_type")
    assert_config = step_data.get("assert_config", {})

    if action_type == "assert_exists":
        return await self._assert_exists(step_data, driver)
    elif action_type == "assert_not_exists":
        return await self._assert_not_exists(step_data, driver)
    elif action_type == "assert_text":
        return await self._assert_text(step_data, driver)
    else:
        logger.warning(f"未知断言类型: {action_type}")
        return TaskResult.FAILED

async def _assert_exists(
    self,
    step_data: Dict,
    driver: AndroidDriver
) -> TaskResult:
    """断言元素存在"""
    element = step_data.get("element")
    locators = element.get("locators", [])

    element_info = await self._find_element(driver, locators)
    if element_info:
        logger.info(f"✅ 断言通过: 元素存在")
        return TaskResult.PASSED
    else:
        logger.error(f"❌ 断言失败: 元素不存在")
        return TaskResult.FAILED
```

#### 元素查找策略
```python
async def _find_element(
    self,
    driver: AndroidDriver,
    locators: List[Dict]
) -> Optional[Dict]:
    """根据定位符数组查找元素"""
    for locator in locators:
        locator_type = locator.get("type")
        value = locator.get("value")

        try:
            if locator_type == "resource-id":
                element = await driver.find_element_by_id(value)
            elif locator_type == "xpath":
                element = await driver.find_element_by_xpath(value)
            elif locator_type == "text":
                element = await driver.find_element_by_text(value)
            elif locator_type == "class":
                element = await driver.find_element_by_class(value)
            else:
                continue

            if element:
                return element

        except Exception as e:
            logger.debug(f"定位符失败: {locator_type}={value}, {e}")
            continue

    return None
```

---

### 5. ADB服务 (ADBService)

#### ADB通信封装
```python
class ADBService:
    """ADB通信服务"""

    def __init__(self, adb_path: str = "adb"):
        self.adb_path = adb_path
        self._devices_cache: Dict[str, DeviceInfo] = {}

    async def execute_command(
        self,
        args: List[str],
        timeout: int = 30
    ) -> str:
        """执行ADB命令"""
        cmd = [self.adb_path] + args
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )

            if proc.returncode != 0:
                raise ADBError(stderr.decode())

            return stdout.decode()

        except asyncio.TimeoutError:
            proc.kill()
            raise ADBError(f"命令超时: {' '.join(cmd)}")

    async def list_devices(self) -> List[DeviceInfo]:
        """获取设备列表"""
        output = await self.execute_command(["devices", "-l"])
        devices = []

        for line in output.splitlines()[1:]:
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                status = parts[1]

                # 解析设备信息
                device_info = await self._get_device_info(serial)
                devices.append(device_info)

        return devices

    async def _get_device_info(self, serial: str) -> DeviceInfo:
        """获取设备详细信息"""
        # 获取品牌
        brand = await self.execute_command([
            "-s", serial, "shell", "getprop", "ro.product.brand"
        ]).strip()

        # 获取型号
        model = await self.execute_command([
            "-s", serial, "shell", "getprop", "ro.product.model"
        ]).strip()

        # 获取Android版本
        android_version = await self.execute_command([
            "-s", serial, "shell", "getprop",
            "ro.build.version.release"
        ]).strip()

        return DeviceInfo(
            serial=serial,
            brand=brand,
            model=model,
            android_version=android_version
        )

    async def get_dom_xml(self, serial: str) -> str:
        """获取设备DOM XML"""
        dom_xml = await self.execute_command([
            "-s", serial,
            "shell", "uiautomator", "dump",
            "/sdcard/window_dump.xml"
        ])

        xml_content = await self.execute_command([
            "-s", serial,
            "shell", "cat", "/sdcard/window_dump.xml"
        ])

        return xml_content

    async def tap(
        self,
        serial: str,
        x: int,
        y: int
    ):
        """点击屏幕坐标"""
        await self.execute_command([
            "-s", serial,
            "shell", "input", "tap", str(x), str(y)
        ])

    async def input_text(
        self,
        serial: str,
        text: str
    ):
        """输入文本"""
        # 转义特殊字符
        escaped_text = text.replace(" ", "%s")
        await self.execute_command([
            "-s", serial,
            "shell", "input", "text", escaped_text
        ])

    async def swipe(
        self,
        serial: str,
        x1: int, y1: int,
        x2: int, y2: int,
        duration: int = 500
    ):
        """滑动屏幕"""
        await self.execute_command([
            "-s", serial,
            "shell", "input",
            "swipe",
            str(x1), str(y1),
            str(x2), str(y2),
            str(duration)
        ])
```

---

### 6. 数据库客户端 (DatabaseClient)

#### 数据库操作
```python
class DatabaseClient:
    """数据库客户端 - 与后端数据库交互"""

    def __init__(self, db_path: str = "testflow.db"):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None

    async def connect(self):
        """连接数据库"""
        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row

    async def close(self):
        """关闭连接"""
        if self.connection:
            await self.connection.close()

    async def fetch_pending_runs(self) -> List[Dict]:
        """获取待执行的任务"""
        cursor = await self.connection.execute("""
            SELECT
                r.id,
                r.execution_type,
                r.target_id,
                r.device_serial,
                r.priority,
                r.timeout,
                r.retry_count,
                r.max_retries
            FROM runs r
            WHERE r.status = 'pending'
            ORDER BY r.priority DESC, r.created_at ASC
            LIMIT 10
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_run_status(
        self,
        run_id: int,
        status: str,
        result: Optional[str] = None
    ):
        """更新执行状态"""
        await self.connection.execute("""
            UPDATE runs
            SET status = ?,
                result = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, result, run_id))
        await self.connection.commit()

    async def append_run_log(
        self,
        run_id: int,
        log_entry: Dict
    ):
        """追加执行日志"""
        log_json = json.dumps(log_entry)
        await self.connection.execute("""
            UPDATE runs
            SET logs = CASE
                WHEN logs IS NULL THEN ?
                ELSE logs || ',' || ?
            END
            WHERE id = ?
        """, (log_json, log_json, run_id))
        await self.connection.commit()

    async def get_testcase_data(
        self,
        testcase_id: int
    ) -> Dict:
        """获取测试用例数据"""
        cursor = await self.connection.execute("""
            SELECT
                tc.id,
                tc.name,
                tc.priority,
                tc.timeout,
                tc.params,
                s.id as setup_flow_id,
                m.id as main_flow_id,
                t.id as teardown_flow_id
            FROM testcases tc
            LEFT JOIN testcase_flow sf ON tc.id = sf.testcase_id
                AND sf.flow_type = 'setup'
            LEFT JOIN testcase_flow mf ON tc.id = mf.testcase_id
                AND mf.flow_type = 'main'
            LEFT JOIN testcase_flow tf ON tc.id = tf.testcase_id
                AND tf.flow_type = 'teardown'
            LEFT JOIN flows s ON sf.flow_id = s.id
            LEFT JOIN flows m ON mf.flow_id = m.id
            LEFT JOIN flows t ON tf.flow_id = t.id
            WHERE tc.id = ?
        """, (testcase_id,))
        row = await cursor.fetchone()
        return dict(row) if row else {}
```

---

### 7. WebSocket客户端 (WebSocketClient)

#### 状态推送
```python
class ExecutorWebSocketClient:
    """WebSocket客户端 - 推送执行状态到后端"""

    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.reconnect_interval = 5

    async def connect(self):
        """连接到后端WebSocket"""
        while True:
            try:
                self.ws = await websockets.connect(
                    f"{self.backend_url}/api/v1/ws/executor"
                )
                logger.info("✅ WebSocket连接成功")
                break
            except Exception as e:
                logger.error(f"WebSocket连接失败: {e}")
                logger.info(f"{self.reconnect_interval}秒后重试...")
                await asyncio.sleep(self.reconnect_interval)

    async def send_status_update(
        self,
        status: str,
        metadata: Optional[Dict] = None
    ):
        """发送状态更新"""
        if not self.ws:
            return

        message = {
            "type": "status_update",
            "status": status,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }

        await self.ws.send(json.dumps(message))

    async def send_log_entry(
        self,
        run_id: int,
        log_entry: Dict
    ):
        """发送日志条目"""
        if not self.ws:
            return

        message = {
            "type": "log_entry",
            "run_id": run_id,
            "log": log_entry,
            "timestamp": datetime.now().isoformat()
        }

        await self.ws.send(json.dumps(message))

    async def send_task_progress(
        self,
        run_id: int,
        current_step: int,
        total_steps: int
    ):
        """发送任务进度"""
        if not self.ws:
            return

        message = {
            "type": "task_progress",
            "run_id": run_id,
            "progress": {
                "current": current_step,
                "total": total_steps,
                "percent": int(current_step / total_steps * 100)
            },
            "timestamp": datetime.now().isoformat()
        }

        await self.ws.send(json.dumps(message))
```

---

### 8. 设备自动发现 (DeviceAutoDiscovery)

#### 设备扫描
```python
class DeviceAutoDiscovery:
    """设备自动发现服务"""

    def __init__(
        self,
        adb_service: ADBService,
        ws_client: ExecutorWebSocketClient
    ):
        self.adb_service = adb_service
        self.ws_client = ws_client
        self._scan_task: Optional[asyncio.Task] = None
        self._known_devices: Set[str] = set()

    async def start_background_scan(self):
        """启动后台扫描任务"""
        self._scan_task = asyncio.create_task(self._scan_loop())

    async def _scan_loop(self):
        """扫描循环"""
        while True:
            try:
                await self._scan_and_register()
                await asyncio.sleep(10)  # 每10秒扫描一次
            except Exception as e:
                logger.error(f"设备扫描失败: {e}")
                await asyncio.sleep(30)  # 出错后等待30秒

    async def _scan_and_register(self):
        """扫描并注册设备"""
        devices = await self.adb_service.list_devices()
        current_serials = {d.serial for d in devices}

        # 发现新设备
        new_devices = current_serials - self._known_devices
        for serial in new_devices:
            device = next(d for d in devices if d.serial == serial)
            await self._register_device(device)
            self._known_devices.add(serial)

        # 设备断开
        disconnected = self._known_devices - current_serials
        for serial in disconnected:
            await self._unregister_device(serial)
            self._known_devices.discard(serial)

    async def _register_device(self, device: DeviceInfo):
        """注册设备到后端"""
        await self.ws_client.send_json({
            "type": "device_discovered",
            "device": {
                "serial": device.serial,
                "name": f"{device.brand} {device.model}",
                "status": "online",
                "brand": device.brand,
                "model": device.model,
                "android_version": device.android_version
            }
        })
        logger.info(f"✅ 设备已注册: {device.serial}")

    async def _unregister_device(self, serial: str):
        """注销设备"""
        await self.ws_client.send_json({
            "type": "device_disconnected",
            "serial": serial
        })
        logger.info(f"❌ 设备已断开: {serial}")
```

---

## 执行流程详解

### 1. 单步骤执行流程

```
┌──────────────────────────────────────────────────────┐
│  Step Execution Flow                                │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. 解析步骤数据                                     │
│     ├── action_type: "click"                        │
│     ├── element: { name, locators }                 │
│     └── wait_after_ms: 300                          │
│                      ↓                               │
│  2. 查找元素                                         │
│     ├── 尝试 resource-id                            │
│     ├── 失败 → 尝试 xpath                           │
│     └── 失败 → 返回 FAILED                           │
│                      ↓                               │
│  3. 执行操作                                         │
│     └── driver.click(element_info)                  │
│                      ↓                               │
│  4. 等待 (wait_after_ms)                            │
│     └── asyncio.sleep(300/1000)                     │
│                      ↓                               │
│  5. 返回结果                                         │
│     └── TaskResult.PASSED                           │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 2. 流程执行流程

```
┌──────────────────────────────────────────────────────┐
│  Flow Execution Flow                                │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. 加载流程数据                                     │
│     ├── flow.name                                    │
│     └── flow.steps[]                                 │
│                      ↓                               │
│  2. 遍历执行步骤                                     │
│     for i, step in enumerate(steps):                │
│       ├── 3. 执行步骤                                │
│       │      result = await execute_step(step)      │
│       │                                              │
│       ├── 4. 检查结果                                │
│       │      if result == FAILED:                   │
│       │        if step.continue_on_error:           │
│       │          continue  # 继续下一步             │
│       │        else:                                │
│       │          break  # 停止执行                  │
│       │                                              │
│       └── 5. 更新进度                                │
│              await ws.send_progress(i+1, len(steps)) │
│                      ↓                               │
│  3. 返回流程结果                                     │
│     └── TaskResult.PASSED / FAILED                  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 3. 测试用例执行流程

```
┌──────────────────────────────────────────────────────┐
│  Testcase Execution Flow                            │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. 加载用例数据                                     │
│     ├── testcase.name                                │
│     ├── testcase.setup_flows[]                       │
│     ├── testcase.main_flows[]                        │
│     └── testcase.teardown_flows[]                    │
│                      ↓                               │
│  2. 执行Setup流程                                    │
│     for flow in setup_flows:                        │
│       result = await execute_flow(flow)             │
│       if result == FAILED:                          │
│         return FAILED  # Setup失败则停止             │
│                      ↓                               │
│  3. 执行Main流程                                     │
│     for flow in main_flows:                         │
│       result = await execute_flow(flow)             │
│       if result == FAILED:                          │
│         main_failed = True                          │
│         break                                        │
│                      ↓                               │
│  4. 执行Teardown流程 (无论Main成功与否)             │
│     for flow in teardown_flows:                     │
│       await execute_flow(flow)                      │
│                      ↓                               │
│  5. 返回最终结果                                     │
│     if main_failed:                                  │
│       return FAILED                                  │
│     else:                                            │
│       return PASSED                                  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 4. 套件执行流程

```
┌──────────────────────────────────────────────────────┐
│  Suite Execution Flow                               │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. 加载套件数据                                     │
│     ├── suite.name                                   │
│     ├── suite.testcases[]                            │
│     └── suite.parallel_execution                     │
│                      ↓                               │
│  2. 串行执行 (parallel_execution=false)             │
│     results = []                                     │
│     for tc in testcases:                            │
│       result = await execute_testcase(tc)           │
│       results.append(result)                        │
│                                                      │
│  3. 并行执行 (parallel_execution=true)              │
│     tasks = [                                        │
│       execute_testcase(tc)                          │
│       for tc in testcases                           │
│     ]                                                │
│     results = await asyncio.gather(*tasks)          │
│                      ↓                               │
│  4. 汇总结果                                         │
│     passed = sum(1 for r in results if r == PASSED) │
│     failed = sum(1 for r in results if r == FAILED) │
│     total = len(results)                             │
│                      ↓                               │
│  5. 生成报告                                         │
│     return {                                         │
│       "total": total,                                │
│       "passed": passed,                              │
│       "failed": failed,                              │
│       "pass_rate": passed/total*100                 │
│     }                                                │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 工作线程机制

### Worker Loop

```python
async def _worker(self):
    """工作线程 - 从队列获取任务并执行"""
    logger.info("🔄 启动工作线程")

    while self.is_running:
        try:
            # 1. 从队列获取任务
            task = await self.execution_queue.get()

            # 2. 执行任务
            await self._execute_task(task)

            # 3. 标记任务完成
            self.execution_queue.task_done(task.id)

        except asyncio.CancelledError:
            logger.info("🛑 工作线程已取消")
            break
        except Exception as e:
            logger.error(f"❌ 工作线程错误: {e}")
            await asyncio.sleep(1)

    logger.info("✅ 工作线程已停止")

async def _execute_task(self, task: ExecutionTask):
    """执行单个任务"""
    logger.info(f"🚀 开始执行任务: {task.id}")

    try:
        # 1. 更新状态为RUNNING
        await self.db_client.update_run_status(
            task.id, "running"
        )

        # 2. 设置当前任务ID（用于日志）
        set_current_task_id(task.id)

        # 3. 执行任务
        result = await task.execute(self)

        # 4. 更新最终状态
        await self.db_client.update_run_status(
            task.id,
            "completed",
            result.value
        )

        # 5. 清除当前任务ID
        clear_current_task_id()

    except Exception as e:
        logger.error(f"❌ 任务执行异常: {e}")
        await self.db_client.update_run_status(
            task.id,
            "failed"
        )
```

---

## 日志处理机制

### 后端日志处理器

```python
class BackendLogHandler(logging.Handler):
    """自定义日志处理器 - 发送日志到后端"""

    def __init__(
        self,
        task_queue_client: TaskQueueClient
    ):
        super().__init__()
        self.task_queue_client = task_queue_client

    def emit(self, record: logging.LogRecord):
        """发送日志记录"""
        try:
            log_entry = {
                "level": record.levelname,
                "message": record.getMessage(),
                "timestamp": datetime.fromtimestamp(
                    record.created
                ).isoformat(),
                "logger": record.name,
                "task_id": getattr(record, 'task_id', None)
            }

            # 异步发送
            asyncio.create_task(
                self.task_queue_client.send_log(log_entry)
            )

        except Exception:
            self.handleError(record)

# 使用示例
logger = logging.getLogger(__name__)
logger.info("这是一条日志")  # 自动发送到后端
```

### 日志上下文

```python
def set_current_task_id(task_id: str):
    """设置当前任务ID"""
    context_var.set(task_id)

def clear_current_task_id():
    """清除当前任务ID"""
    context_var.set(None)

# 日志记录时自动附加
logger.info("执行步骤", extra={"task_id": get_current_task_id()})
```

---

## 配置管理

### 环境变量配置

```bash
# .env
# 日志配置
LOG_LEVEL=INFO

# ADB配置
ADB_PATH=adb
ADB_TIMEOUT=30
DEFAULT_DEVICE_TIMEOUT=120

# 执行配置
MAX_CONCURRENT_EXECUTIONS=5
EXECUTION_TIMEOUT=3600
STEP_TIMEOUT=60

# 截图配置
SCREENSHOT_ON_FAILURE=true
SCREENSHOT_DIR=./screenshots

# 重试配置
MAX_RETRIES=3
RETRY_DELAY=1.0

# 后端连接
BACKEND_WS_URL=ws://localhost:8000
DATABASE_PATH=../backend/testflow.db
```

### 配置类

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """执行引擎配置"""

    # 日志
    log_level: str = "INFO"

    # ADB
    adb_path: str = "adb"
    adb_timeout: int = 30
    default_device_timeout: int = 120

    # 执行
    max_concurrent_executions: int = 5
    execution_timeout: int = 3600
    step_timeout: int = 60

    # 截图
    screenshot_on_failure: bool = True
    screenshot_dir: str = "./screenshots"

    # 重试
    max_retries: int = 3
    retry_delay: float = 1.0

    # 后端
    backend_ws_url: str = "ws://localhost:8000"
    database_path: str = "../backend/testflow.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 故障处理

### 重试机制

```python
async def _execute_with_retry(
    self,
    task: ExecutionTask
) -> TaskResult:
    """带重试的执行"""
    last_error = None

    for attempt in range(task.max_retries + 1):
        try:
            # 执行任务
            result = await task.execute(self)

            if result == TaskResult.PASSED:
                return result

            last_error = Exception(f"任务失败: {result}")

        except Exception as e:
            last_error = e
            logger.warning(f"第{attempt + 1}次尝试失败: {e}")

        # 重试延迟
        if attempt < task.max_retries:
            await asyncio.sleep(settings.retry_delay)

    # 所有重试都失败
    logger.error(f"任务失败，已重试{task.max_retries}次")
    return TaskResult.FAILED
```

### 超时处理

```python
async def _execute_with_timeout(
    self,
    task: ExecutionTask
) -> TaskResult:
    """带超时的执行"""
    try:
        result = await asyncio.wait_for(
            task.execute(self),
            timeout=task.timeout
        )
        return result

    except asyncio.TimeoutError:
        logger.error(f"任务执行超时: {task.timeout}秒")
        await task.cancel()
        return TaskResult.FAILED
```

### 错误恢复

```python
async def _handle_device_error(
    self,
    device_serial: str,
    error: Exception
):
    """处理设备错误"""
    logger.error(f"设备错误: {device_serial}, {error}")

    # 1. 标记设备离线
    await self.db_client.update_device_status(
        device_serial, "offline"
    )

    # 2. 发送通知
    await self.ws_client.send_json({
        "type": "device_error",
        "serial": device_serial,
        "error": str(error)
    })

    # 3. 尝试重启ADB
    try:
        await self.adb_service.restart_adb()
        logger.info("ADB重启成功")
    except Exception as e:
        logger.error(f"ADB重启失败: {e}")
```

---

## 性能优化

### 1. 异步I/O
- 所有数据库操作使用 aiosqlite
- 所有ADB命令使用 asyncio.subprocess
- WebSocket通信使用 websockets库

### 2. 连接池
```python
# ADB连接复用
class ADBConnectionPool:
    def __init__(self, max_connections: int = 10):
        self.pool = asyncio.Queue(maxsize=max_connections)
        self.active_connections: Dict[str, ADBService] = {}

    async def get_connection(self, serial: str) -> ADBService:
        if serial in self.active_connections:
            return self.active_connections[serial]

        adb = ADBService()
        await adb.connect(serial)
        self.active_connections[serial] = adb
        return adb
```

### 3. 批量操作
```python
# 批量更新状态
async def batch_update_status(
    self,
    updates: List[Tuple[int, str]]
):
    """批量更新执行状态"""
    await self.db_client.executemany("""
        UPDATE runs
        SET status = ?
        WHERE id = ?
    """, updates)
    await self.db_client.commit()
```

---

## 监控指标

### 执行统计
```python
class ExecutionMetrics:
    """执行指标统计"""

    def __init__(self):
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_duration = 0
        self.avg_duration = 0

    def record_execution(
        self,
        duration: float,
        result: TaskResult
    ):
        """记录执行数据"""
        self.total_executions += 1
        self.total_duration += duration
        self.avg_duration = (
            self.total_duration / self.total_executions
        )

        if result == TaskResult.PASSED:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

    def get_success_rate(self) -> float:
        """计算成功率"""
        if self.total_executions == 0:
            return 0.0
        return (
            self.successful_executions /
            self.total_executions * 100
        )
```

---

## 总结

TestFlow Executor 是一个高效、可靠的测试执行引擎，具有以下核心优势：

1. **独立架构**: 独立进程运行，不依赖Web服务
2. **异步执行**: asyncio实现高并发执行
3. **智能队列**: 支持并发控制和优先级调度
4. **实时通信**: WebSocket推送执行状态和日志
5. **设备管理**: 自动发现和注册设备
6. **容错机制**: 重试、超时、错误恢复
7. **可扩展性**: 支持多种操作类型和平台

适用于中小型团队的Android自动化测试执行需求，特别适合需要长时间稳定运行和实时监控的场景。
