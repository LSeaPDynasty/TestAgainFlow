"""
修复错误的project_id（从1931改为1）

运行方式：
    python scripts/fix_project_id.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import engine
from sqlalchemy import text


def fix_project_id():
    """修复错误的project_id"""
    print("开始修复错误的project_id...")
    print("=" * 60)

    try:
        with engine.connect() as conn:
            print("\n修复: 将 project_id=1931 的记录改为 project_id=1")

            tables = ['testcases', 'suites', 'run_history', 'screens', 'elements', 'steps', 'flows']

            total_fixed = 0

            for table in tables:
                # 检查表是否存在project_id列
                result = conn.execute(text(f"PRAGMA table_info({table})"))
                columns = [row[1] for row in result]

                if 'project_id' not in columns:
                    continue

                # 修复错误的project_id
                count = conn.execute(text(
                    f"UPDATE {table} SET project_id = 1 WHERE project_id = 1931"
                )).rowcount

                conn.commit()

                if count > 0:
                    print(f"✓ {table}: 修复了 {count} 条记录")
                    total_fixed += count

            print("\n" + "=" * 60)
            print(f"✅ 修复完成！共修复 {total_fixed} 条记录")

            # 显示最终统计
            print(f"\n📊 项目1（1931）下的最终数据统计:")
            for table in ['testcases', 'suites', 'screens', 'elements', 'steps', 'flows']:
                result = conn.execute(text(f"PRAGMA table_info({table})"))
                columns = [row[1] for row in result]

                if 'project_id' in columns:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table} WHERE project_id = 1"))
                    count = result.scalar()
                    print(f"  - {table}: {count} 条")

    except Exception as e:
        print(f"\n❌ 修复失败: {str(e)}")
        raise


if __name__ == "__main__":
    fix_project_id()
