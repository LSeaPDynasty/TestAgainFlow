"""
Run Screenshot model
存储执行失败的截图信息
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel


class RunScreenshot(BaseModel):
    """执行截图模型"""
    __tablename__ = 'run_screenshots'

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), ForeignKey('run_history.task_id'), nullable=False, index=True)
    filename = Column(String(255), nullable=False, comment='截图文件名')
    filepath = Column(String(500), nullable=False, comment='截图文件路径')
    step_name = Column(String(200), nullable=True, comment='步骤名称')
    timestamp = Column(String(50), nullable=True, comment='时间戳')
    created_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<RunScreenshot(task_id='{self.task_id}', filename='{self.filename}')>"
