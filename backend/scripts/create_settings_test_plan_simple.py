# -*- coding: utf-8 -*-
"""
创建设置界面测试计划
按照功能模块组织测试套件和测试用例
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.project import Project
from app.models.suite import Suite, SuiteTestcase
from app.models.testcase import Testcase
from app.models.test_plan import TestPlan, TestPlanSuite
from datetime import datetime

# 设置界面功能模块定义
SETTINGS_MODULES = [
    # 作业管理模块
    {
        'category': '作业管理',
        'items': [
            '项目管理',
            '坐标系统',
            '记录点库',
            '点校正',
            '基线计算',
        ]
    },
    # 数据采集模块
    {
        'category': '数据采集',
        'items': [
            '采集设置',
            '点位存储',
            '代码定义',
            '属性定义',
        ]
    },
    # 仪器设置模块
    {
        'category': '仪器设置',
        'items': [
            '接收机设置',
            '天线设置',
            '电台设置',
            '数据链路',
        ]
    },
    # 网络模块
    {
        'category': '网络设置',
        'items': [
            '网络配置',
            'CORS账号',
            'NTRIP设置',
            'APN设置',
        ]
    },
    # 存储模块
    {
        'category': '存储设置',
        'items': [
            '数据导出',
            '文件管理',
            '备份恢复',
            '格式化存储',
        ]
    },
    # 显示模块
    {
        'category': '显示设置',
        'items': [
            '地图设置',
            '界面主题',
            '语言设置',
            '单位设置',
        ]
    },
    # 其他设置
    {
        'category': '其他设置',
        'items': [
            '系统信息',
            '关于',
            '帮助文档',
            '用户反馈',
        ]
    },
]


def create_test_plan():
    """创建完整的测试计划"""
    db = SessionLocal()
    try:
        # 获取项目（使用项目ID=1）
        project = db.query(Project).filter(Project.id == 1).first()
        if not project:
            print("Error: Project ID 1 not found!")
            return

        print(f"Using project: {project.name} (ID: {project.id})")

        # 1. 创建测试计划
        test_plan = TestPlan(
            name="设置界面功能测试计划",
            description="测试设置界面下所有功能模块，验证每个功能入口可以正常打开。执行策略：串行执行每个套件，每个套件测试一个功能模块的所有功能项。",
            execution_strategy="sequential",
            max_parallel_tasks=1,
            enabled=True,
            project_id=project.id,
        )
        db.add(test_plan)
        db.flush()
        print(f"\n{'='*60}")
        print(f"Created test plan: {test_plan.name}")
        print(f"ID: {test_plan.id}")
        print(f"Description: {test_plan.description}")
        print(f"Execution strategy: {test_plan.execution_strategy}")
        print(f"{'='*60}")

        # 2. 为每个功能模块创建测试套件和测试用例
        suite_order = 0
        total_suites = 0
        total_testcases = 0

        for module in SETTINGS_MODULES:
            category = module['category']
            items = module['items']

            # 为该模块创建测试套件
            suite = Suite(
                name=f"设置-{category}",
                description=f"测试设置界面中{category}模块的所有功能项：{', '.join(items)}",
                project_id=project.id,
            )
            db.add(suite)
            db.flush()
            total_suites += 1
            print(f"\n[{total_suites}] Created suite: {suite.name} (ID: {suite.id})")
            print(f"    Description: {suite.description}")

            # 将套件添加到测试计划
            test_plan_suite = TestPlanSuite(
                test_plan_id=test_plan.id,
                suite_id=suite.id,
                order_index=suite_order,
                enabled=True,
            )
            db.add(test_plan_suite)
            suite_order += 1

            # 为该模块的每个功能项创建测试用例
            for idx, item_name in enumerate(items, 1):
                testcase = Testcase(
                    name=f"{category}-{item_name}",
                    description=f"验证设置界面中[{category}]模块的[{item_name}]功能可以正常打开。\n"
                               f"测试步骤：\n"
                               f"1. 启动应用\n"
                               f"2. 点击设置按钮进入设置界面\n"
                               f"3. 点击[{item_name}]功能项\n"
                               f"4. 验证界面成功打开\n"
                               f"5. 返回上级\n"
                               f"6. 重启应用（后置流程）",
                    project_id=project.id,
                )
                db.add(testcase)
                db.flush()
                total_testcases += 1

                # 关联测试用例到套件
                suite_testcase = SuiteTestcase(
                    suite_id=suite.id,
                    testcase_id=testcase.id,
                    order_index=idx - 1,  # 从0开始
                    enabled=True,
                )
                db.add(suite_testcase)

                print(f"    [{idx}] Created testcase: {testcase.name} (ID: {testcase.id})")

        db.commit()
        print(f"\n{'='*60}")
        print(f"测试计划创建完成！")
        print(f"{'='*60}")
        print(f"测试计划名称: {test_plan.name}")
        print(f"测试计划ID: {test_plan.id}")
        print(f"所属项目: {project.name} (ID: {project.id})")
        print(f"执行策略: {test_plan.execution_strategy}")
        print(f"包含套件数: {total_suites}")
        print(f"包含测试用例数: {total_testcases}")
        print(f"{'='*60}")

        # 打印套件列表
        print(f"\n套件列表：")
        for idx, module in enumerate(SETTINGS_MODULES, 1):
            category = module['category']
            items_count = len(module['items'])
            print(f"  {idx}. 设置-{category} ({items_count}个测试用例)")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    create_test_plan()
