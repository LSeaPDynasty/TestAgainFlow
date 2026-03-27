"""
检查数据库状态
"""
import sqlite3
from datetime import datetime

db_path = 'testflow.db'

print(f"检查数据库: {db_path}")
print(f"当前时间: {datetime.now()}")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print(f"\n数据库中的表 ({len(tables)} 个):")
for table in tables:
    print(f"  - {table}")

print("\n" + "=" * 60)
print("各表数据统计:")
print("=" * 60)

for table in tables:
    # 跳过系统表
    if table.startswith('sqlite_'):
        continue

    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:30s}: {count:6d} 行")
    except Exception as e:
        print(f"{table:30s}: 错误 - {str(e)}")

print("\n" + "=" * 60)
print("关键表详情:")
print("=" * 60)

# 检查关键表
key_tables = ['projects', 'screens', 'elements', 'steps', 'flows', 'testcases', 'suites', 'devices']

for table in key_tables:
    if table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]

            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                row = cursor.fetchone()
                print(f"\n{table} ({count} 行) - 示例数据:")
                print(f"  第一行: {row}")
            else:
                print(f"\n{table}: 空表")
        except Exception as e:
            print(f"\n{table}: 检查失败 - {str(e)}")
    else:
        print(f"\n{table}: 表不存在")

# 检查 alembic 版本
print("\n" + "=" * 60)
print("迁移状态:")
print("=" * 60)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
if cursor.fetchone():
    cursor.execute("SELECT version_num FROM alembic_version")
    version = cursor.fetchone()
    print(f"当前迁移版本: {version[0] if version else '无'}")
else:
    print("alembic_version 表不存在 - 数据库未使用迁移管理")

conn.close()

print("\n" + "=" * 60)
print("检查完成!")
