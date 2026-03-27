"""Add testcase_items table for unified flow/step mixed ordering

Revision ID: 003_add_testcase_items
Revises: 002_add_ai_tables
Create Date: 2026-03-25

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_testcase_items'
down_revision: Union[str, None] = '002_add_ai_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create testcase_items table
    op.create_table(
        'testcase_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('testcase_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.Enum('flow', 'step', name='testcase_item_type_enum'), nullable=False),
        sa.Column('flow_id', sa.Integer(), nullable=True),
        sa.Column('step_id', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('continue_on_error', sa.Boolean(), nullable=True),
        sa.Column('params', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['testcase_id'], ['testcases.id'], name=op.f('fk_testcase_items_testcase_id_testcases'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['flow_id'], ['flows.id'], name=op.f('fk_testcase_items_flow_id_flows'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['step_id'], ['steps.id'], name=op.f('fk_testcase_items_step_id_steps'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "(item_type = 'flow' AND flow_id IS NOT NULL AND step_id IS NULL) OR "
            "(item_type = 'step' AND step_id IS NOT NULL AND flow_id IS NULL)",
            name='check_testcase_item_consistency'
        ),
        comment='Unified testcase execution sequence supporting flow/step mixed ordering'
    )

    # Create indexes for performance
    op.create_index('ix_testcase_items_testcase_id', 'testcase_items', ['testcase_id'])
    op.create_index('ix_testcase_items_order_index', 'testcase_items', ['testcase_id', 'order_index'])
    op.create_index('ix_testcase_items_item_type', 'testcase_items', ['item_type'])


def downgrade() -> None:
    # Drop testcase_items table
    op.drop_index('ix_testcase_items_item_type', 'testcase_items')
    op.drop_index('ix_testcase_items_order_index', 'testcase_items')
    op.drop_index('ix_testcase_items_testcase_id', 'testcase_items')
    op.drop_table('testcase_items')
