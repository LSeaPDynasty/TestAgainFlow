"""
Database Client
直接连接后端数据库，读取执行任务
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

# 添加backend目录到路径，以便导入backend的模型
# 从 executor/app/services/db_client.py 到项目根目录
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent  # 回退4级到testflow根目录
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

logger = logging.getLogger(__name__)


class DatabaseClient:
    """
    数据库客户端 - 直接连接SQLite数据库
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            # 默认使用backend的数据库
            db_path = backend_path / "testflow.db"

        # 确保路径是绝对路径
        self.db_path = Path(db_path).resolve()
        self._connection = None

        logger.info(f"数据库路径: {self.db_path}")

    async def connect(self):
        """连接数据库"""
        import aiosqlite
        self._connection = await aiosqlite.connect(str(self.db_path))
        self._connection.row_factory = aiosqlite.Row
        logger.info(f"✅ 连接数据库: {self.db_path}")

    async def close(self):
        """关闭数据库连接"""
        if self._connection:
            await self._connection.close()
            logger.info("✅ 数据库连接已关闭")

    async def get_pending_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取待执行的运行任务"""
        if not self._connection:
            await self.connect()

        query = """
            SELECT id, run_type, target_id, device_serial, status, config
            FROM runs
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT ?
        """

        cursor = await self._connection.execute(query, (limit,))
        rows = await cursor.fetchall()

        executions = []
        for row in rows:
            executions.append({
                "id": row["id"],
                "run_type": row["run_type"],
                "target_id": row["target_id"],
                "device_serial": row["device_serial"],
                "status": row["status"],
                "config": row["config"] or {}
            })

        if executions:
            logger.info(f"📋 找到 {len(executions)} 个待执行任务")

        return executions

    async def update_execution_status(
        self,
        task_id: str,
        status: str,
        duration: float = None
    ):
        """更新执行状态"""
        if not self._connection:
            await self.connect()

        updates = ["result = ?"]
        params = [status]

        if duration is not None:
            updates.append("duration = ?")
            params.append(duration)

        # 如果是完成状态，设置完成时间
        if status in ['pass', 'fail', 'cancelled', 'timeout', 'error']:
            updates.append("finished_at = ?")
            params.append(datetime.utcnow().isoformat())

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())

        params.append(task_id)

        query = f"UPDATE run_history SET {', '.join(updates)} WHERE task_id = ?"
        await self._connection.execute(query, params)
        await self._connection.commit()

        logger.debug(f"✏️  更新执行状态: {task_id} -> {status}")

    async def update_suite_statistics(
        self,
        task_id: str,
        success_count: int = 0,
        failed_count: int = 0,
        skipped_count: int = 0
    ):
        """更新套件执行统计"""
        if not self._connection:
            await self.connect()

        query = """
            UPDATE run_history
            SET success_count = ?,
                failed_count = ?,
                skipped_count = ?,
                updated_at = ?
            WHERE task_id = ?
        """
        await self._connection.execute(query, (
            success_count,
            failed_count,
            skipped_count,
            datetime.utcnow().isoformat(),
            task_id
        ))
        await self._connection.commit()

        logger.debug(f"✏️  更新套件统计: {task_id} - {success_count}通过, {failed_count}失败, {skipped_count}跳过")

    async def get_step(self, step_id: int) -> Optional[Dict[str, Any]]:
        """获取步骤详情"""
        if not self._connection:
            await self.connect()

        query = """
            SELECT s.*, sc.name as screen_name, el.name as element_name
            FROM steps s
            LEFT JOIN screens sc ON s.screen_id = sc.id
            LEFT JOIN elements el ON s.element_id = el.id
            WHERE s.id = ?
        """

        cursor = await self._connection.execute(query, (step_id,))
        row = await cursor.fetchone()

        if row:
            return dict(row)
        return None

    async def get_steps_batch(self, step_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """批量获取步骤详情 - ✅ 解决N+1查询问题"""
        if not step_ids:
            return {}

        if not self._connection:
            await self.connect()

        # 使用IN查询一次性获取所有步骤
        placeholders = ','.join('?' * len(step_ids))
        query = f"""
            SELECT s.*, sc.name as screen_name, el.name as element_name
            FROM steps s
            LEFT JOIN screens sc ON s.screen_id = sc.id
            LEFT JOIN elements el ON s.element_id = el.id
            WHERE s.id IN ({placeholders})
        """

        cursor = await self._connection.execute(query, step_ids)
        rows = await cursor.fetchall()

        # 构建ID -> step数据的映射
        steps_map = {row['id']: dict(row) for row in rows}
        return steps_map

    async def get_flow(self, flow_id: int) -> Optional[Dict[str, Any]]:
        """获取流程详情"""
        if not self._connection:
            await self.connect()

        query = """
            SELECT f.*
            FROM flows f
            WHERE f.id = ?
        """

        cursor = await self._connection.execute(query, (flow_id,))
        row = await cursor.fetchone()

        if row:
            flow = dict(row)
            # 获取流程步骤
            steps_query = """
                SELECT fs.*, s.*, sc.name as screen_name, el.name as element_name,
                       l.type as locator_type, l.value as locator_value
                FROM flow_steps fs
                JOIN steps s ON fs.step_id = s.id
                LEFT JOIN screens sc ON s.screen_id = sc.id
                LEFT JOIN elements el ON s.element_id = el.id
                LEFT JOIN locators l ON el.id = l.element_id AND l.priority = 1
                WHERE fs.flow_id = ?
                ORDER BY fs.order_index
            """
            cursor = await self._connection.execute(steps_query, (flow_id,))
            steps_rows = await cursor.fetchall()

            # 构建步骤列表，包含locator信息
            steps_list = []
            for row in steps_rows:
                step_dict = dict(row)
                # 构建locator字典
                if step_dict.get('locator_type') and step_dict.get('locator_value'):
                    step_dict['locator'] = {
                        'type': step_dict['locator_type'],
                        'value': step_dict['locator_value']
                    }
                steps_list.append(step_dict)

            flow["steps"] = steps_list

            return flow
        return None

    async def get_testcase(self, testcase_id: int) -> Optional[Dict[str, Any]]:
        """获取用例详情"""
        if not self._connection:
            await self.connect()

        query = "SELECT * FROM testcases WHERE id = ?"
        cursor = await self._connection.execute(query, (testcase_id,))
        row = await cursor.fetchone()

        if row:
            testcase = dict(row)

            # 获取setup flows
            setup_query = """
                SELECT tf.*, f.name, f.flow_type
                FROM testcase_flows tf
                JOIN flows f ON tf.flow_id = f.id
                WHERE tf.testcase_id = ? AND tf.flow_role = 'setup'
                ORDER BY tf.order_index
            """
            cursor = await self._connection.execute(setup_query, (testcase_id,))
            testcase["setup_flows"] = [dict(row) for row in await cursor.fetchall()]

            # 获取main flows
            main_query = """
                SELECT tf.*, f.name, f.flow_type
                FROM testcase_flows tf
                JOIN flows f ON tf.flow_id = f.id
                WHERE tf.testcase_id = ? AND tf.flow_role = 'main'
                ORDER BY tf.order_index
            """
            cursor = await self._connection.execute(main_query, (testcase_id,))
            testcase["main_flows"] = [dict(row) for row in await cursor.fetchall()]

            # 获取teardown flows
            teardown_query = """
                SELECT tf.*, f.name, f.flow_type
                FROM testcase_flows tf
                JOIN flows f ON tf.flow_id = f.id
                WHERE tf.testcase_id = ? AND tf.flow_role = 'teardown'
                ORDER BY tf.order_index
            """
            cursor = await self._connection.execute(teardown_query, (testcase_id,))
            testcase["teardown_flows"] = [dict(row) for row in await cursor.fetchall()]

            # 获取 testcase_items（新增）
            items_query = """
                SELECT ti.*,
                       f.name as flow_name,
                       s.name as step_name,
                       s.action_type as step_action_type
                FROM testcase_items ti
                LEFT JOIN flows f ON ti.flow_id = f.id
                LEFT JOIN steps s ON ti.step_id = s.id
                WHERE ti.testcase_id = ?
                ORDER BY ti.order_index
            """
            cursor = await self._connection.execute(items_query, (testcase_id,))
            testcase["testcase_items"] = [dict(row) for row in await cursor.fetchall()]

            return testcase
        return None

    async def get_suite(self, suite_id: int) -> Optional[Dict[str, Any]]:
        """获取套件详情"""
        if not self._connection:
            await self.connect()

        query = "SELECT * FROM suites WHERE id = ?"
        cursor = await self._connection.execute(query, (suite_id,))
        row = await cursor.fetchone()

        if row:
            suite = dict(row)

            # 获取套件中的用例
            testcases_query = """
                SELECT st.*, tc.name
                FROM suite_testcases st
                JOIN testcases tc ON st.testcase_id = tc.id
                WHERE st.suite_id = ?
                ORDER BY st.order_index
            """
            cursor = await self._connection.execute(testcases_query, (suite_id,))
            suite["testcases"] = [dict(row) for row in await cursor.fetchall()]

            return suite
        return None

    async def create_run_log(self, execution_id: int, level: str, message: str):
        """创建运行日志"""
        if not self._connection:
            await self.connect()

        query = """
            INSERT INTO run_logs (run_id, level, message, created_at)
            VALUES (?, ?, ?, ?)
        """
        await self._connection.execute(query, (
            execution_id,
            level,
            message,
            datetime.utcnow().isoformat()
        ))
        await self._connection.commit()
