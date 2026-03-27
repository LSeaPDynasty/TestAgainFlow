"""add test_plans table for test plan management

Revision ID: 005_add_test_plans
Revises: 004_add_action_types
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_add_test_plans'
down_revision = '004_add_action_types'
branch_labels = None
depends_on = None


def upgrade():
    """Create test plan tables"""

    # 1. 测试计划主表
    op.create_table(
        'test_plans',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=200), nullable=False, comment='测试计划名称'),
        sa.Column('description', sa.Text(), nullable=True, comment='测试计划描述'),
        sa.Column('execution_strategy', sa.String(length=20), nullable=False, default='sequential', comment='执行策略: sequential or parallel'),
        sa.Column('max_parallel_tasks', sa.Integer(), nullable=False, default=1, comment='并行执行时的最大并发数'),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True, comment='是否启用'),
        sa.Column('project_id', sa.Integer(), nullable=True, comment='项目ID'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('name'),
        comment='测试计划主表'
    )
    op.create_index('idx_test_plans_project', 'test_plans', ['project_id'])
    op.create_index('idx_test_plans_enabled', 'test_plans', ['enabled'])

    # 2. 测试计划-套件关联表（支持顺序）
    op.create_table(
        'test_plan_suites',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('test_plan_id', sa.Integer(), nullable=False, comment='测试计划ID'),
        sa.Column('suite_id', sa.Integer(), nullable=False, comment='套件ID'),
        sa.Column('order_index', sa.Integer(), nullable=False, comment='套件在计划中的执行顺序'),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True, comment='是否启用此套件'),
        sa.Column('execution_config', sa.Text(), nullable=True, comment='JSON格式的套件级执行配置'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['test_plan_id'], ['test_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['suite_id'], ['suites.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('test_plan_id', 'suite_id', name='uq_test_plan_suite'),
        comment='测试计划-套件关联表'
    )
    op.create_index('idx_test_plan_suites_plan', 'test_plan_suites', ['test_plan_id'])
    op.create_index('idx_test_plan_suites_suite', 'test_plan_suites', ['suite_id'])
    op.create_index('idx_test_plan_suites_order', 'test_plan_suites', ['order_index'])

    # 3. 测试计划-用例自定义顺序表（可选）
    op.create_table(
        'test_plan_testcase_orders',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('test_plan_suite_id', sa.Integer(), nullable=False, comment='测试计划套件关联ID'),
        sa.Column('testcase_id', sa.Integer(), nullable=False, comment='用例ID'),
        sa.Column('order_index', sa.Integer(), nullable=False, comment='用例在该套件内的执行顺序'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['test_plan_suite_id'], ['test_plan_suites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['testcase_id'], ['testcases.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('test_plan_suite_id', 'testcase_id', name='uq_plan_suite_testcase'),
        comment='测试计划-用例自定义顺序表'
    )
    op.create_index('idx_test_plan_testcase_orders_plan_suite', 'test_plan_testcase_orders', ['test_plan_suite_id'])
    op.create_index('idx_test_plan_testcase_orders_testcase', 'test_plan_testcase_orders', ['testcase_id'])
    op.create_index('idx_test_plan_testcase_orders_order', 'test_plan_testcase_orders', ['order_index'])


def downgrade():
    """Rollback migration"""
    op.drop_table('test_plan_testcase_orders')
    op.drop_table('test_plan_suites')
    op.drop_table('test_plans')
