"""
Run Log Model
存储执行日志
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel


class RunLog(BaseModel):
    """执行日志模型"""
    __tablename__ = "run_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("run_history.task_id"), nullable=False, index=True)
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    timestamp = Column(Float, nullable=False)  # Unix timestamp

    # Suite execution fields
    testcase_id = Column(Integer, nullable=True)  # 用例ID（套件执行时使用）
    testcase_name = Column(String(200), nullable=True)  # 用例名称
    testcase_result = Column(String(20), nullable=True)  # 用例结果：passed/failed/skipped

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RunLog(task_id='{self.task_id}', level='{self.level}', message='{self.message[:50]}...')>"
