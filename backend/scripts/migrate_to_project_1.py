"""
将所有现有数据迁移到项目ID=1（项目名称：1931）

运行方式：
    python scripts/migrate_to_project_1.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import engine
from sqlalchemy import text


def migrate_to_project_1():
    """将所有现有数据迁移到项目ID=1"""
    project_id = 1
    print(f"开始将现有数据迁移到项目 {project_id}（项目名称：1931）...")
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
            # 检查项目是否存在
            print(f"\n1️⃣ 检查项目 {project_id} 是否存在...")
            result = conn.execute(text(f"SELECT name FROM projects WHERE id = {project_id}"))
            project = result.fetchone()

            if not project:
                print(f"❌ 项目 {project_id} 不存在！")
                return

            project_name = project[0]
            print(f"✅ 项目存在: {project_name}")

            # 检查现有表
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            existing_tables = [row[0] for row in result]

            print(f"\n2️⃣ 开始迁移数据...")

            total_updated = 0
            migration_details = {}

            for table_name in tables_to_migrate:
                if table_name not in existing_tables:
                    print(f"⚠️ {table_name} 表不存在，跳过")
                    continue

                # 检查是否有 project_id 列
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result]

                if 'project_id' not in columns:
                    print(f"⚠️ {table_name} 表没有 project_id 列，先添加列...")
                    conn.execute(text(
                        f"ALTER TABLE {table_name} ADD COLUMN project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL"
                    ))
                    conn.commit()
                    print(f"✓ {table_name} 表已添加 project_id 列")

                # 更新数据（只更新 project_id 为 NULL 的记录）
                count = conn.execute(text(
                    f"UPDATE {table_name} SET project_id = {project_id} WHERE project_id IS NULL"
                )).rowcount

                conn.commit()
                total_updated += count
                migration_details[table_name] = count

                if count > 0:
                    print(f"✓ {table_name}: 更新了 {count} 条记录")
                else:
                    print(f"ℹ {table_name}: 所有记录都已有 project_id")

            print("\n" + "=" * 60)
            print(f"✅ 迁移完成！")
            print(f"\n迁移详情:")
            for table, count in migration_details.items():
                if count > 0:
                    print(f"  - {table}: {count} 条")
            print(f"\n总计: {total_updated} 条记录已设置 project_id = {project_id}")
            print(f"项目名称: {project_name}")

            # 显示各表的统计
            print(f"\n📊 项目{project_id}（{project_name}）下的数据统计:")
            for table_name in ['testcases', 'suites', 'screens', 'elements', 'steps', 'flows']:
                if table_name not in existing_tables:
                    continue

                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = [row[1] for row in result]

                if 'project_id' in columns:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE project_id = {project_id}"))
                    count = result.scalar()
                    print(f"  - {table_name}: {count} 条")

    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        raise


if __name__ == "__main__":
    migrate_to_project_1()
