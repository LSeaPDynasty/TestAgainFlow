"""
性能优化验证测试
验证N+1查询问题是否已修复
"""
import time
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.repositories.element_repo import ElementRepository
from app.repositories.step_repo import StepRepository


def test_element_query_performance():
    """测试元素查询性能"""
    db: Session = SessionLocal()
    try:
        repo = ElementRepository(db)

        # 测试查询性能
        start = time.time()
        elements, total = repo.list_with_details(limit=100)
        elapsed = time.time() - start

        print(f"✅ 查询{total}个元素耗时: {elapsed:.3f}秒")
        print(f"   平均每个元素: {(elapsed/total*1000):.2f}毫秒" if total > 0 else "")

        # 验证结果
        assert len(elements) <= 100, "返回结果数量应该不超过limit"
        assert total >= 0, "总数应该非负"

        # 验证每个元素都有locators字段
        for elem in elements:
            assert 'locators' in elem, f"元素{elem['id']}缺少locators字段"

        # 性能基准：100个元素应该在1秒内完成
        if total >= 10:
            assert elapsed < 1.0, f"查询{total}个元素耗时{elapsed:.3f}秒，超过1秒阈值"

        print(f"✅ 元素查询性能测试通过！")
        return True

    finally:
        db.close()


def test_step_batch_query():
    """测试步骤批量查询"""
    from executor.app.services.db_client import DatabaseClient
    import asyncio

    async def test():
        db_client = DatabaseClient()
        await db_client.connect()

        # 测试批量查询
        step_ids = [1, 2, 3, 4, 5]  # 测试5个步骤

        start = time.time()
        steps_map = await db_client.get_steps_batch(step_ids)
        elapsed = time.time() - start

        print(f"✅ 批量查询{len(step_ids)}个步骤耗时: {elapsed:.3f}秒")

        # 验证结果
        assert len(steps_map) <= len(step_ids), "返回结果数量不应该超过请求数量"
        for step_id in step_ids:
            if step_id in steps_map:
                assert 'id' in steps_map[step_id], "步骤数据应该包含id字段"

        # 性能基准：5个步骤应该在0.5秒内完成
        assert elapsed < 0.5, f"批量查询耗时{elapsed:.3f}秒，超过0.5秒阈值"

        print(f"✅ 步骤批量查询测试通过！")
        await db_client.close()
        return True

    return asyncio.run(test())


if __name__ == '__main__':
    print("=" * 60)
    print("性能优化验证测试")
    print("=" * 60)

    print("\n测试1: 元素查询性能...")
    test_element_query_performance()

    print("\n测试2: 步骤批量查询...")
    test_step_batch_query()

    print("\n" + "=" * 60)
    print("✅ 所有性能测试通过！")
    print("=" * 60)
