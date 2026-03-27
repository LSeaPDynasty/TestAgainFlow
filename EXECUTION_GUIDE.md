"""
套件执行增强：在每个用例前后自动执行恢复操作

使用方法：
1. 在 Suite 数据中添加 recovery_flow_id 字段
2. 指定一个用于恢复的 Flow（如回到首页）
3. 执行套件时会在每个用例前后自动执行恢复
"""

# 在 _execute_suite 方法中添加恢复逻辑
async def _execute_suite_with_recovery(self, task: ExecutionTask) -> TaskResult:
    """执行套件（带自动恢复）"""
    suite_data = await self.db_client.get_suite(task.target_id)

    if not suite_data:
        raise ValueError(f"套件不存在: {task.target_id}")

    suite_name = suite_data.get('name', 'Unknown')
    testcases = suite_data.get("testcases", [])
    recovery_flow_id = suite_data.get("recovery_flow_id")  # 新增字段

    passed = 0
    failed = 0
    skipped = 0

    for idx, testcase_info in enumerate(testcases, 1):
        if not testcase_info.get("enabled", 1):
            skipped += 1
            continue

        testcase_name = testcase_info.get('name', 'Unknown')

        # 【用例前恢复】执行恢复流程，确保从干净状态开始
        if recovery_flow_id:
            task.log(f"\n🔄 用例前恢复")
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "INFO",
                "message": f"执行用例前恢复: {testcase_name}",
                "timestamp": asyncio.get_event_loop().time()
            })

            recovery_task = ExecutionTask(
                task_id=f"{task.task_id}_recovery_before_{idx}",
                execution_type=ExecutionType.FLOW,
                target_id=recovery_flow_id,
                device_serial=task.device_serial,
                config=task.config
            )

            await self._execute_flow(recovery_task)

        # 执行用例
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
        elif result == TaskResult.FAILED:
            failed += 1

        # 【用例后恢复】确保为下一个用例准备干净状态
        # 注意：用例自己的 teardown 已经在 _execute_testcase 中执行了
        if recovery_flow_id:
            task.log(f"\n🔄 用例后恢复")
            await self.task_queue_client.send_task_log(task.task_id, {
                "level": "INFO",
                "message": f"执行用例后恢复: {testcase_name}",
                "timestamp": asyncio.get_event_loop().time()
            })

            recovery_task = ExecutionTask(
                task_id=f"{task.task_id}_recovery_after_{idx}",
                execution_type=ExecutionType.FLOW,
                target_id=recovery_flow_id,
                device_serial=task.device_serial,
                config=task.config
            )

            await self._execute_flow(recovery_task)

    # 返回套件执行结果
    if failed > 0:
        return TaskResult.FAILED
    return TaskResult.PASSED
