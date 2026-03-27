"""add test_plan run type support

Revision ID: 006_add_test_plan_run_type
Revises: 005_add_test_plans
Create Date: 2026-03-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_test_plan_run_type'
down_revision = '005_add_test_plans'
branch_labels = None
depends_on = None


def upgrade():
    """Add test_plan type to run_history enum"""

    # SQLite doesn't support ALTER ENUM directly, need to recreate the table
    # Step 1: Create new table with updated enum
    op.create_table(
        'run_history_new',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.String(length=100), nullable=False, unique=True, comment='Task ID, unique'),
        sa.Column('type', sa.Enum('testcase', 'suite', 'test_plan', name='run_type_enum_v2'), nullable=False, comment='Run type'),
        sa.Column('target_id', sa.Integer(), nullable=True, comment='Target ID (null for test_plan)'),
        sa.Column('target_name', sa.String(length=200), nullable=True, comment='Target name (null for test_plan)'),
        sa.Column('result', sa.Enum('pending', 'running', 'pass', 'fail', 'cancelled', 'timeout', name='run_result_enum'), nullable=False, default='pending', comment='Execution result'),
        sa.Column('returncode', sa.Integer(), nullable=True, comment='Process return code'),
        sa.Column('duration', sa.Float(), nullable=True, comment='Execution duration in seconds'),
        sa.Column('profile_id', sa.Integer(), nullable=True, comment='Profile ID used'),
        sa.Column('profile_name', sa.String(length=100), nullable=True, comment='Profile name'),
        sa.Column('device_serial', sa.String(length=100), nullable=True, comment='Device serial used'),
        sa.Column('device_name', sa.String(length=100), nullable=True, comment='Device name'),
        sa.Column('has_screenshots', sa.Integer(), nullable=False, default=0, comment='Has screenshots flag'),
        sa.Column('log_path', sa.String(length=500), nullable=True, comment='Log file path'),
        sa.Column('project_id', sa.Integer(), nullable=True, comment='Project ID'),
        sa.Column('total_count', sa.Integer(), nullable=False, default=0, comment='Total testcase count'),
        sa.Column('success_count', sa.Integer(), nullable=False, default=0, comment='Success count'),
        sa.Column('failed_count', sa.Integer(), nullable=False, default=0, comment='Failed count'),
        sa.Column('skipped_count', sa.Integer(), nullable=False, default=0, comment='Skipped count'),
        sa.Column('test_plan_id', sa.Integer(), nullable=True, comment='Test Plan ID (for test_plan runs)'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='Start time'),
        sa.Column('finished_at', sa.DateTime(), nullable=True, comment='Finish time'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['test_plan_id'], ['test_plans.id'], ondelete='SET NULL'),
        comment='Run execution history records'
    )

    # Step 2: Copy data from old table to new table
    op.execute("""
        INSERT INTO run_history_new
        (id, task_id, type, target_id, target_name, result, returncode, duration,
         profile_id, profile_name, device_serial, device_name, has_screenshots,
         log_path, project_id, total_count, success_count, failed_count, skipped_count,
         started_at, finished_at, created_at, updated_at)
        SELECT id, task_id, type, target_id, target_name, result, returncode, duration,
               profile_id, profile_name, device_serial, device_name, has_screenshots,
               log_path, project_id, total_count, success_count, failed_count, skipped_count,
               started_at, finished_at, created_at, updated_at
        FROM run_history
    """)

    # Step 3: Drop old table
    op.drop_table('run_history')

    # Step 4: Rename new table
    op.rename_table('run_history_new', 'run_history')

    # Step 5: Recreate indexes
    op.create_index('ix_run_history_task_id', 'run_history', ['task_id'])
    op.create_index('ix_run_history_type', 'run_history', ['type'])
    op.create_index('ix_run_history_result', 'run_history', ['result'])
    op.create_index('ix_run_history_device_serial', 'run_history', ['device_serial'])
    op.create_index('ix_run_history_test_plan_id', 'run_history', ['test_plan_id'])


def downgrade():
    """Rollback migration"""

    # Revert to original enum (remove test_plan and test_plan_id)
    op.create_table(
        'run_history_old',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.String(length=100), nullable=False, unique=True),
        sa.Column('type', sa.Enum('testcase', 'suite', name='run_type_enum'), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('target_name', sa.String(length=200), nullable=False),
        sa.Column('result', sa.Enum('pending', 'running', 'pass', 'fail', 'cancelled', 'timeout', name='run_result_enum'), nullable=False, default='pending'),
        sa.Column('returncode', sa.Integer(), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('profile_id', sa.Integer(), nullable=True),
        sa.Column('profile_name', sa.String(length=100), nullable=True),
        sa.Column('device_serial', sa.String(length=100), nullable=True),
        sa.Column('device_name', sa.String(length=100), nullable=True),
        sa.Column('has_screenshots', sa.Integer(), nullable=False, default=0),
        sa.Column('log_path', sa.String(length=500), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('total_count', sa.Integer(), nullable=False, default=0),
        sa.Column('success_count', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_count', sa.Integer(), nullable=False, default=0),
        sa.Column('skipped_count', sa.Integer(), nullable=False, default=0),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
    )

    op.execute("""
        INSERT INTO run_history_old
        (id, task_id, type, target_id, target_name, result, returncode, duration,
         profile_id, profile_name, device_serial, device_name, has_screenshots,
         log_path, project_id, total_count, success_count, failed_count, skipped_count,
         started_at, finished_at, created_at, updated_at)
        SELECT id, task_id, type, target_id, target_name, result, returncode, duration,
               profile_id, profile_name, device_serial, device_name, has_screenshots,
               log_path, project_id, total_count, success_count, failed_count, skipped_count,
               started_at, finished_at, created_at, updated_at
        FROM run_history
        WHERE type IN ('testcase', 'suite')
    """)

    op.drop_table('run_history')
    op.rename_table('run_history_old', 'run_history')

    op.create_index('ix_run_history_task_id', 'run_history', ['task_id'])
    op.create_index('ix_run_history_type', 'run_history', ['type'])
    op.create_index('ix_run_history_result', 'run_history', ['result'])
    op.create_index('ix_run_history_device_serial', 'run_history', ['device_serial'])
