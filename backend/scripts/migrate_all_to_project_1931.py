"""
完整的数据库迁移脚本：将所有现有数据设置 project_id = 1931

运行方式：
    python scripts/migrate_all_to_project_1931.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import engine
from sqlalchemy import text


def migrate():
    """将所有现有数据迁移到项目 1931"""
    print("开始将现有数据迁移到项目 1931...")
    print("=" * 60)

    tables_to_migrate = [
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

            total_updated = 0

            for table_name in tables_to_migrate:
                if table_name not in existing_tables:
                    print(f"⚠ {table_name} 表不存在，跳过")
                    continue

                # 检查是否有 project_id 列
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result]

                if 'project_id' not in columns:
                    print(f"⚠ {table_name} 表没有 project_id 列，跳过")
                    continue

                # 更新数据
                count = conn.execute(text(
                    f"UPDATE {table_name} SET project_id = 1931 WHERE project_id IS NULL"
                )).rowcount

                conn.commit()
                total_updated += count

                if count > 0:
                    print(f"✓ {table_name}: 更新了 {count} 条记录")
                else:
                    print(f"ℹ {table_name}: 所有记录都已有 project_id")

        print("\n" + "=" * 60)
        print(f"✅ 迁移完成！共更新 {total_updated} 条记录")
        print("所有现有数据已设置 project_id = 1931")

    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        raise


if __name__ == "__main__":
    migrate()
