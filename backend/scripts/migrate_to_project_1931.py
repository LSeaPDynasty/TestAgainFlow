"""
数据库迁移脚本：将现有数据设置 project_id = 1931

运行方式：
    python scripts/migrate_to_project_1931.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal
from app.models.testcase import Testcase
from app.models.suite import Suite
from app.models.run_history import RunHistory


def migrate():
    """迁移现有数据到项目 1931"""
    db = SessionLocal()

    try:
        # 更新 testcases
        testcase_count = db.query(Testcase).filter(Testcase.project_id.is_(None)).count()
        if testcase_count > 0:
            db.query(Testcase).filter(Testcase.project_id.is_(None)).update({"project_id": 1931})
            print(f"✓ 更新了 {testcase_count} 个测试用例的 project_id")
        else:
            print("ℹ 所有测试用例都已有 project_id")

        # 更新 suites
        suite_count = db.query(Suite).filter(Suite.project_id.is_(None)).count()
        if suite_count > 0:
            db.query(Suite).filter(Suite.project_id.is_(None)).update({"project_id": 1931})
            print(f"✓ 更新了 {suite_count} 个测试套件的 project_id")
        else:
            print("ℹ 所有测试套件都已有 project_id")

        # 更新 run_history
        run_count = db.query(RunHistory).filter(RunHistory.project_id.is_(None)).count()
        if run_count > 0:
            db.query(RunHistory).filter(RunHistory.project_id.is_(None)).update({"project_id": 1931})
            print(f"✓ 更新了 {run_count} 条执行记录的 project_id")
        else:
            print("ℹ 所有执行记录都已有 project_id")

        db.commit()
        print("\n✅ 迁移完成！所有现有数据已设置 project_id = 1931")

    except Exception as e:
        db.rollback()
        print(f"\n❌ 迁移失败: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("开始数据迁移...")
    print("=" * 60)
    migrate()
