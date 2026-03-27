"""add action_types table for executor capability registration

Revision ID: 004_add_action_types
Revises: 003_add_testcase_items
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '004_add_action_types'
down_revision = '003_add_testcase_items'
branch_labels = None
depends_on = None


def upgrade():
    """创建操作类型表和执行器表"""

    # 1. 执行器表（记录执行器实例）
    op.create_table(
        'executors',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('executor_id', sa.String(length=100), nullable=False, comment='执行器唯一标识'),
        sa.Column('executor_version', sa.String(length=20), nullable=False, comment='执行器版本'),
        sa.Column('hostname', sa.String(length=100), comment='主机名'),
        sa.Column('ip_address', sa.String(length=50), comment='IP地址'),
        sa.Column('last_seen', sa.DateTime(), comment='最后心跳时间'),
        sa.Column('is_online', sa.Boolean(), comment='是否在线'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        comment='执行器实例表'
    )
    op.create_index('ix_executors_executor_id', 'executors', ['executor_id'], unique=True)
    op.create_index('ix_executors_is_online', 'executors', ['is_online'])

    # 2. 操作类型表（累积所有见过的操作类型）
    op.create_table(
        'action_types',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('type_code', sa.String(length=50), nullable=False, comment='操作类型代码'),
        sa.Column('display_name', sa.String(length=100), nullable=False, comment='显示名称'),
        sa.Column('category', sa.String(length=50), comment='分类'),
        sa.Column('description', sa.String(length=500), comment='描述'),
        sa.Column('color', sa.String(length=20), comment='前端显示颜色'),
        sa.Column('requires_element', sa.Boolean(), comment='是否需要元素'),
        sa.Column('requires_value', sa.Boolean(), comment='是否需要参数值'),
        sa.Column('config_schema', sa.Text(), comment='配置Schema(JSON)'),
        sa.Column('first_seen_executor_id', sa.String(length=100), comment='首次注册的执行器ID'),
        sa.Column('first_seen_at', sa.DateTime(), comment='首次发现时间'),
        sa.Column('is_deprecated', sa.Boolean(), comment='是否已废弃'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        comment='操作类型表（累积，只增不减）'
    )
    op.create_index('ix_action_types_type_code', 'action_types', ['type_code'], unique=True)
    op.create_index('ix_action_types_category', 'action_types', ['category'])
    op.create_index('ix_action_types_is_deprecated', 'action_types', ['is_deprecated'])

    # 3. 执行器-操作类型关联表（多对多）
    op.create_table(
        'executor_action_capabilities',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('executor_id', sa.String(length=100), nullable=False),
        sa.Column('action_type_code', sa.String(length=50), nullable=False),
        sa.Column('executor_version', sa.String(length=20), comment='注册时的执行器版本'),
        sa.Column('registered_at', sa.DateTime(), comment='注册时间'),
        sa.Column('implementation_version', sa.String(length=20), comment='实现版本'),
        sa.ForeignKeyConstraint(['executor_id'], ['executors.executor_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['action_type_code'], ['action_types.type_code'], ondelete='CASCADE'),
        comment='执行器操作能力关联表'
    )
    op.create_index('ix_executor_actions_executor_id', 'executor_action_capabilities', ['executor_id'])
    op.create_index('ix_executor_actions_action_code', 'executor_action_capabilities', ['action_type_code'])
    op.create_index('ix_executor_actions_unique', 'executor_action_capabilities', ['executor_id', 'action_type_code'], unique=True)


def downgrade():
    """回滚迁移"""
    op.drop_table('executor_action_capabilities')
    op.drop_table('action_types')
    op.drop_table('executors')
