"""
检查项目1931的数据情况

运行方式：
    python scripts/check_project_1931.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from sqlalchemy import text


def check_project_1931():
    """检查项目1931的数据"""
    db = SessionLocal()

    try:
        print("=" * 60)
        print("检查项目1931的数据情况")
        print("=" * 60)

        # 1. 检查项目是否存在
        print("\n1️⃣ 检查项目是否存在...")
        result = db.execute(text("SELECT * FROM projects WHERE id = 1931"))
        project = result.fetchone()

        if project:
            print(f"✅ 项目存在:")
            print(f"   ID: {project[0]}")
            print(f"   名称: {project[1]}")
            print(f"   描述: {project[2]}")
            print(f"   状态: {project[3]}")
        else:
            print("❌ 项目1931不存在！")
            print("\n请先创建项目1931，或者将现有数据的project_id设置为实际存在的项目ID")

        # 2. 检查各表的数据
        tables = ['testcases', 'suites', 'screens', 'elements', 'steps', 'flows']

        for table in tables:
            print(f"\n2️⃣ 检查 {table} 表...")

            # 检查表是否有project_id列
            result = db.execute(text(f"PRAGMA table_info({table})"))
            columns = [row[1] for row in result]

            if 'project_id' not in columns:
                print(f"   ⚠️ {table} 表没有 project_id 列")
                continue

            # 统计总数
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            total = result.scalar()

            # 统计有project_id的记录数
            result = db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE project_id IS NOT NULL"))
            with_project_id = result.scalar()

            # 统计project_id=1931的记录数
            result = db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE project_id = 1931"))
            is_1931 = result.scalar()

            # 统计project_id IS NULL的记录数
            result = db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE project_id IS NULL"))
            null_count = result.scalar()

            print(f"   总记录数: {total}")
            print(f"   有project_id: {with_project_id}")
            print(f"   project_id=1931: {is_1931}")
            print(f"   project_id=NULL: {null_count}")

            # 显示一些示例数据
            if table == 'testcases':
                result = db.execute(text(
                    "SELECT id, name, project_id FROM testcases LIMIT 5"
                ))
                print(f"\n   示例数据:")
                for row in result:
                    print(f"   - ID: {row[0]}, 名称: {row[1]}, project_id: {row[2]}")

        # 3. 检查是否有其他项目
        print(f"\n3️⃣ 检查所有项目...")
        result = db.execute(text("SELECT id, name FROM projects"))
        projects = result.fetchall()

        if projects:
            print(f"   现有 {len(projects)} 个项目:")
            for p in projects:
                print(f"   - ID: {p[0]}, 名称: {p[1]}")
        else:
            print("   ⚠️ 数据库中没有项目")

        print("\n" + "=" * 60)
        print("✅ 检查完成！")
        print("\n建议操作：")

        if not project:
            print("1. 在前端创建项目1931")
            print("2. 或者修改脚本，将数据迁移到实际存在的项目ID")
        else:
            null_counts = {}
            for table in tables:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE project_id IS NULL"))
                null_counts[table] = result.scalar()

            tables_with_null = [t for t, c in null_counts.items() if c > 0]

            if tables_with_null:
                print(f"1. 以下表的记录需要设置project_id: {', '.join(tables_with_null)}")
                print("2. 运行: python scripts/migrate_all_to_project_1931.py")

    except Exception as e:
        print(f"\n❌ 检查失败: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    check_project_1931()
