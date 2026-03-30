"""
Executor and Action Type models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base


class Executor(Base):
    """执行器实例表"""
    __tablename__ = 'executors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    executor_id = Column(String(100), unique=True, nullable=False, index=True, comment='执行器唯一标识')
    executor_version = Column(String(20), nullable=False, comment='执行器版本')
    hostname = Column(String(100), comment='主机名')
    ip_address = Column(String(50), comment='IP地址')
    last_seen = Column(DateTime, default=datetime.now(timezone.utc), comment='最后心跳时间')
    is_online = Column(Boolean, default=True, index=True, comment='是否在线')
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # 关系
    capabilities = relationship("ExecutorActionCapability", back_populates="executor", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Executor(id={self.executor_id}, version={self.executor_version}, online={self.is_online})>"


class ActionType(Base):
    """操作类型表（累积，只增不减）"""
    __tablename__ = 'action_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_code = Column(String(50), unique=True, nullable=False, index=True, comment='操作类型代码')
    display_name = Column(String(100), nullable=False, comment='显示名称')
    category = Column(String(50), index=True, comment='分类')
    description = Column(String(500), comment='描述')
    color = Column(String(20), comment='前端显示颜色')
    requires_element = Column(Boolean, default=False, comment='是否需要元素')
    requires_value = Column(Boolean, default=False, comment='是否需要参数值')
    config_schema = Column(Text, comment='配置Schema(JSON)')
    first_seen_executor_id = Column(String(100), comment='首次注册的执行器ID')
    first_seen_at = Column(DateTime, default=datetime.now(timezone.utc), comment='首次发现时间')
    is_deprecated = Column(Boolean, default=False, index=True, comment='是否已废弃')
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # 关系
    executor_capabilities = relationship("ExecutorActionCapability", back_populates="action_type", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ActionType({self.type_code}, category={self.category})>"


class ExecutorActionCapability(Base):
    """执行器-操作类型关联表（多对多）"""
    __tablename__ = 'executor_action_capabilities'

    id = Column(Integer, primary_key=True, autoincrement=True)
    executor_id = Column(String(100), ForeignKey('executors.executor_id', ondelete='CASCADE'), nullable=False, index=True)
    action_type_code = Column(String(50), ForeignKey('action_types.type_code', ondelete='CASCADE'), nullable=False, index=True)
    executor_version = Column(String(20), comment='注册时的执行器版本')
    registered_at = Column(DateTime, default=datetime.now(timezone.utc), comment='注册时间')
    implementation_version = Column(String(20), comment='实现版本')

    # 关系
    executor = relationship("Executor", back_populates="capabilities")
    action_type = relationship("ActionType", back_populates="executor_capabilities")

    def __repr__(self):
        return f"<ExecutorActionCapability(executor={self.executor_id}, action={self.action_type_code})>"
