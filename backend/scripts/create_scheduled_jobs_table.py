"""
创建scheduled_jobs表

运行方式：
    python scripts/create_scheduled_jobs_table.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import engine
from sqlalchemy import text


def create_scheduled_jobs_table():
    """创建scheduled_jobs表"""
    print("Creating scheduled_jobs table...")
    print("=" * 60)

    try:
        with engine.connect() as conn:
            # 检查表是否已存在
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='scheduled_jobs'"
            ))
            if result.fetchone():
                print("INFO: scheduled_jobs table already exists, skipping")
                return

            # 创建表
            conn.execute(text("""
                CREATE TABLE scheduled_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    description TEXT,
                    job_type VARCHAR(50) NOT NULL,
                    target_id INTEGER NOT NULL,
                    cron_expression VARCHAR(100) NOT NULL,
                    device_serial VARCHAR(100),
                    enabled BOOLEAN NOT NULL DEFAULT 1,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    last_run_time DATETIME,
                    next_run_time DATETIME,
                    last_run_status VARCHAR(20),
                    last_run_message TEXT,
                    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
                    created_by INTEGER,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

            print("SUCCESS: scheduled_jobs table created")

            # 创建索引
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_enabled ON scheduled_jobs(enabled)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_status ON scheduled_jobs(status)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_project ON scheduled_jobs(project_id)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_next_run ON scheduled_jobs(next_run_time)"
            ))
            conn.commit()

            print("SUCCESS: Indexes created")

            print("\n" + "=" * 60)
            print("SUCCESS: scheduled_jobs table and indexes created!")

    except Exception as e:
        print(f"\nERROR: Creation failed: {str(e)}")
        raise


if __name__ == "__main__":
    create_scheduled_jobs_table()
