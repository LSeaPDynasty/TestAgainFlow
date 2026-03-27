"""
完整的数据库迁移脚本：为所有相关表添加 project_id 列

运行方式：
    python scripts/add_all_project_columns.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import engine
from sqlalchemy import text


def migrate():
    """为所有相关表添加 project_id 列"""
    print("开始为所有表添加 project_id 列...")
    print("=" * 60)

    # 定义需要添加 project_id 的表
    tables_to_add = [
        'screens',
        'elements',
        'steps',
        'flows',
        'testcases',
        'suites',
        'run_history'
    ]

    try:
        with engine.connect() as conn:
            # 检查现有表
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            existing_tables = [row[0] for row in result]

            print(f"现有表: {existing_tables}\n")

            # 为每个表添加 project_id 列
            for table_name in tables_to_add:
                if table_name in existing_tables:
                    # 检查列是否已存在
                    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                    columns = [row[1] for row in result]

                    if 'project_id' not in columns:
                        try:
                            conn.execute(text(
                                f"ALTER TABLE {table_name} ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL"
                            ))
                            conn.commit()
                            print(f"✓ 已为 {table_name} 表添加 project_id 列")
                        except Exception as e:
                            print(f"✗ {table_name} 表添加列失败: {str(e)}")
                    else:
                        print(f"ℹ {table_name} 表已有 project_id 列")
                else:
                    print(f"⚠ {table_name} 表不存在，跳过")

        print("\n" + "=" * 60)
        print("✅ project_id 列添加完成！")
        print("\n下一步：运行 python scripts/migrate_all_to_project_1931.py 来设置现有数据的项目ID")

    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        raise


if __name__ == "__main__":
    migrate()
