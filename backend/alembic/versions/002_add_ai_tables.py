"""Add AI configuration and logging tables

Revision ID: 002_add_ai_tables
Revises: 001_initial
Create Date: 2026-03-24

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_ai_tables'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ai_configs table
    op.create_table(
        'ai_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        comment='AI provider configurations'
    )
    op.create_index('ix_ai_configs_provider', 'ai_configs', ['provider'])
    op.create_index('ix_ai_configs_is_active', 'ai_configs', ['is_active'])

    # Create ai_request_logs table
    op.create_table(
        'ai_request_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('request_type', sa.String(length=50), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(precision=10), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('request_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='AI request logging for monitoring and cost tracking'
    )
    op.create_index('ix_ai_request_logs_provider', 'ai_request_logs', ['provider'])
    op.create_index('ix_ai_request_logs_status', 'ai_request_logs', ['status'])
    op.create_index('ix_ai_request_logs_created_at', 'ai_request_logs', ['created_at'])
    op.create_index('ix_ai_request_logs_request_hash', 'ai_request_logs', ['request_hash'])

    # Create ai_cache table
    op.create_table(
        'ai_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('response_data', sa.JSON(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_hash'),
        comment='AI response caching'
    )
    op.create_index('ix_ai_cache_expires_at', 'ai_cache', ['expires_at'])

    # Add ai_config_id column to profiles table
    op.add_column('profiles',
                  sa.Column('ai_config_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_profiles_ai_config', 'profiles', 'ai_configs',
                         ['ai_config_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # Drop foreign key and column from profiles
    op.drop_constraint('fk_profiles_ai_config', 'profiles', type_='foreignkey')
    op.drop_column('profiles', 'ai_config_id')

    # Drop ai_cache table
    op.drop_index('ix_ai_cache_expires_at', table_name='ai_cache')
    op.drop_table('ai_cache')

    # Drop ai_request_logs table
    op.drop_index('ix_ai_request_logs_request_hash', table_name='ai_request_logs')
    op.drop_index('ix_ai_request_logs_created_at', table_name='ai_request_logs')
    op.drop_index('ix_ai_request_logs_status', table_name='ai_request_logs')
    op.drop_index('ix_ai_request_logs_provider', table_name='ai_request_logs')
    op.drop_table('ai_request_logs')

    # Drop ai_configs table
    op.drop_index('ix_ai_configs_is_active', table_name='ai_configs')
    op.drop_index('ix_ai_configs_provider', table_name='ai_configs')
    op.drop_table('ai_configs')
