"""
为 suites 表添加 recovery_flow_id 字段

运行方式：
    python scripts/add_recovery_flow.py
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import engine
from sqlalchemy import text


def migrate():
    """添加 recovery_flow_id 列"""
    print("开始添加 recovery_flow_id 列...")
    print("=" * 60)

    try:
        with engine.connect() as conn:
            # 检查列是否已存在
            result = conn.execute(text("PRAGMA table_info(suites)"))
            columns = [row[1] for row in result]

            if 'recovery_flow_id' not in columns:
                conn.execute(text(
                    "ALTER TABLE suites ADD COLUMN recovery_flow_id INTEGER REFERENCES flows(id) ON DELETE SET NULL"
                ))
                conn.commit()
                print("✓ 已为 suites 表添加 recovery_flow_id 列")
            else:
                print("ℹ suites 表已有 recovery_flow_id 列")

        print("\n" + "=" * 60)
        print("✅ 迁移完成！")
        print("\n使用说明：")
        print("1. 在流程管理中创建一个'回到首页'的 Flow")
        print("2. 编辑套件，设置 recovery_flow_id")
        print("3. 执行套件时会在每个用例前后自动执行恢复")

    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        raise


if __name__ == "__main__":
    migrate()
