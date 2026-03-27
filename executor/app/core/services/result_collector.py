"""
Result Collector - 执行结果收集器
聚合和管理测试执行结果
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from ..task import TaskResult

logger = logging.getLogger(__name__)


class ResultCollector:
    """执行结果收集器 - 跟踪和聚合测试执行结果"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置收集器状态"""
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }

    def add_result(self, result: TaskResult, item_info: Dict[str, Any] = None):
        """添加一个执行结果"""
        self.results["total"] += 1

        if result == TaskResult.PASSED:
            self.results["passed"] += 1
        elif result == TaskResult.FAILED:
            self.results["failed"] += 1
            if item_info:
                self.results["errors"].append({
                    "item": item_info,
                    "result": "failed"
                })
        elif result == TaskResult.SKIPPED:
            self.results["skipped"] += 1

    def get_summary(self) -> Dict[str, Any]:
        """获取结果摘要"""
        return {
            "total": self.results["total"],
            "passed": self.results["passed"],
            "failed": self.results["failed"],
            "skipped": self.results["skipped"],
            "errors_count": len(self.results["errors"]),
            "success_rate": (
                self.results["passed"] / self.results["total"] * 100
                if self.results["total"] > 0 else 0
            )
        }

    def get_final_result(self) -> TaskResult:
        """根据收集的结果计算最终结果"""
        if self.results["failed"] > 0:
            return TaskResult.FAILED
        elif self.results["passed"] > 0:
            return TaskResult.PASSED
        else:
            return TaskResult.SKIPPED

    def has_errors(self) -> bool:
        """是否有错误"""
        return self.results["failed"] > 0

    def get_errors(self) -> List[Dict[str, Any]]:
        """获取所有错误"""
        return self.results["errors"]
