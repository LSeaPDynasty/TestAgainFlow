"""
TestcaseItem model - unified execution sequence supporting flow/step mixed ordering
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, JSON, Enum, CheckConstraint
from sqlalchemy.orm import relationship
from .base import BaseModel, Base


class TestcaseItem(BaseModel):
    """
    Testcase execution item - supports mixed flow/step ordering

    Examples:
        Flow → Step → Step → Flow → Step
        [登录流程] → [输入用户名] → [输入密码] → [点击登录] → [断言登录成功]
    """
    __tablename__ = 'testcase_items'

    id = Column(Integer, primary_key=True, comment='Item ID')
    testcase_id = Column(
        Integer,
        ForeignKey('testcases.id', ondelete='CASCADE'),
        nullable=False,
        comment='Parent testcase ID'
    )
    item_type = Column(
        Enum('flow', 'step', name='testcase_item_type_enum'),
        nullable=False,
        comment='Item type: flow or step'
    )
    flow_id = Column(
        Integer,
        ForeignKey('flows.id', ondelete='CASCADE'),
        nullable=True,
        comment='Flow ID (required when item_type=flow)'
    )
    step_id = Column(
        Integer,
        ForeignKey('steps.id', ondelete='CASCADE'),
        nullable=True,
        comment='Step ID (required when item_type=step)'
    )
    order_index = Column(
        Integer,
        nullable=False,
        comment='Execution order (1-based index)'
    )
    enabled = Column(
        Boolean,
        nullable=False,
        default=True,
        comment='Enabled flag (disabled items are skipped)'
    )
    continue_on_error = Column(
        Boolean,
        nullable=True,
        comment='Continue execution on error (overrides step-level setting)'
    )
    params = Column(
        JSON,
        nullable=True,
        comment='Override parameters for flow/step'
    )

    # Relationships
    testcase = relationship('Testcase', back_populates='testcase_items')
    flow = relationship('Flow', foreign_keys=[flow_id])
    step = relationship('Step', foreign_keys=[step_id])

    __table_args__ = (
        # Constraint: flow_id and step_id are mutually exclusive based on item_type
        CheckConstraint(
            "(item_type = 'flow' AND flow_id IS NOT NULL AND step_id IS NULL) OR "
            "(item_type = 'step' AND step_id IS NOT NULL AND flow_id IS NULL)",
            name='check_testcase_item_consistency'
        ),
    )

    def __repr__(self):
        if self.item_type == 'flow':
            return f"<TestcaseItem(id={self.id}, testcase_id={self.testcase_id}, item_type=flow, flow_id={self.flow_id}, order={self.order_index})>"
        else:
            return f"<TestcaseItem(id={self.id}, testcase_id={self.testcase_id}, item_type=step, step_id={self.step_id}, order={self.order_index})>"
