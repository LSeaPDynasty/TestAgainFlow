"""
数据库迁移脚本：添加 project_id 列到相关表

运行方式：
    python scripts/add_project_columns.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal, engine
from sqlalchemy import text


def migrate():
    """添加 project_id 列到相关表"""
    db = SessionLocal()

    try:
        print("开始添加 project_id 列...")
        print("=" * 60)

        # 检查表是否存在
        tables_to_check = ['testcases', 'suites', 'run_history']
        existing_tables = []

        # 使用原生连接检查表是否存在
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            existing_tables = [row[0] for row in result]

        print(f"现有表: {existing_tables}")

        # 为 testcases 表添加 project_id 列
        if 'testcases' in existing_tables:
            try:
                with engine.connect() as conn:
                    # 检查列是否已存在
                    result = conn.execute(text("PRAGMA table_info(testcases)"))
                    columns = [row[1] for row in result]

                    if 'project_id' not in columns:
                        conn.execute(text(
                            "ALTER TABLE testcases ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL"
                        ))
                        conn.commit()
                        print("✓ 已为 testcases 表添加 project_id 列")
                    else:
                        print("ℹ testcases 表已有 project_id 列")
            except Exception as e:
                print(f"✗ testcases 表添加列失败: {str(e)}")

        # 为 suites 表添加 project_id 列
        if 'suites' in existing_tables:
            try:
                with engine.connect() as conn:
                    # 检查列是否已存在
                    result = conn.execute(text("PRAGMA table_info(suites)"))
                    columns = [row[1] for row in result]

                    if 'project_id' not in columns:
                        conn.execute(text(
                            "ALTER TABLE suites ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL"
                        ))
                        conn.commit()
                        print("✓ 已为 suites 表添加 project_id 列")
                    else:
                        print("ℹ suites 表已有 project_id 列")
            except Exception as e:
                print(f"✗ suites 表添加列失败: {str(e)}")

        # 为 run_history 表添加 project_id 列
        if 'run_history' in existing_tables:
            try:
                with engine.connect() as conn:
                    # 检查列是否已存在
                    result = conn.execute(text("PRAGMA table_info(run_history)"))
                    columns = [row[1] for row in result]

                    if 'project_id' not in columns:
                        conn.execute(text(
                            "ALTER TABLE run_history ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL"
                        ))
                        conn.commit()
                        print("✓ 已为 run_history 表添加 project_id 列")
                    else:
                        print("ℹ run_history 表已有 project_id 列")
            except Exception as e:
                print(f"✗ run_history 表添加列失败: {str(e)}")

        print("\n" + "=" * 60)
        print("✅ project_id 列添加完成！")
        print("\n下一步：运行 python scripts/migrate_to_project_1931.py 来设置现有数据的项目ID")

    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
