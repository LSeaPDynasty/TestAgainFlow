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
from app.models.suite import Suite
from app.models.testcase import Testcase
from app.models.testcase_item import TestcaseItem
from app.models.step import Step
from app.models.test_plan import TestPlan, TestPlanSuite
from datetime import datetime

# 设置界面功能模块定义（按常见RTK/测量应用的功能分类）
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
        # 获取或使用默认项目
        project = db.query(Project).filter(Project.id == 1).first()
        if not project:
            print("Project ID 1 not found!")
            return

        print(f"Using project: {project.name} (ID: {project.id})")

        # 1. 创建测试计划
        test_plan = TestPlan(
            name="设置界面功能测试计划",
            description="测试设置界面下所有功能模块，验证每个功能入口可以正常打开",
            execution_strategy="sequential",
            max_parallel_tasks=1,
            enabled=True,
            project_id=project.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(test_plan)
        db.flush()
        print(f"\nCreated test plan: {test_plan.name} (ID: {test_plan.id})")

        # 2. 为每个功能模块创建测试套件和测试用例
        suite_order = 0
        total_testcases = 0

        for module in SETTINGS_MODULES:
            category = module['category']
            items = module['items']

            # 为该模块创建测试套件
            suite = Suite(
                name=f"设置-{category}",
                description=f"测试设置界面中{category}模块的所有功能项",
                project_id=project.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(suite)
            db.flush()
            print(f"\nCreated suite: {suite.name} (ID: {suite.id})")

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
            for item_name in items:
                testcase = create_testcase_for_setting_item(
                    db, suite.id, project.id, category, item_name
                )
                total_testcases += 1
                print(f"  Created testcase: {testcase.name} (ID: {testcase.id})")

        db.commit()
        print(f"\n{'='*60}")
        print(f"测试计划创建完成！")
        print(f"测试计划: {test_plan.name} (ID: {test_plan.id})")
        print(f"包含套件数: {suite_order}")
        print(f"包含测试用例数: {total_testcases}")
        print(f"{'='*60}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def create_testcase_for_setting_item(db, suite_id, project_id, category, item_name):
    """为单个设置项创建测试用例"""
    testcase = Testcase(
        name=f"设置-{category}-{item_name}",
        description=f"验证设置界面中[{category}]模块的[{item_name}]功能可以正常打开",
        suite_id=suite_id,
        project_id=project_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(testcase)
    db.flush()

    # 创建测试步骤
    steps = []

    # 步骤1: 启动应用（前置步骤）
    step_start = Step(
        name="启动应用",
        description="启动被测应用",
        screen_id=1,  # 需要根据实际情况调整
        action_type="start_activity",
        action_value="com.chcnav.rtgh.app/.MainActivity",  # 需要根据实际情况调整
        wait_time=2000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(step_start)
    db.flush()
    steps.append(step_start)

    # 步骤2: 点击设置按钮（进入设置界面）
    step_click_settings = Step(
        name=f"点击设置按钮",
        description="点击进入设置界面",
        screen_id=1,
        action_type="click",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(step_click_settings)
    db.flush()
    steps.append(step_click_settings)

    # 步骤3: 点击具体功能项
    step_click_item = Step(
        name=f"点击{item_name}",
        description=f"在设置界面中点击[{item_name}]功能项",
        screen_id=2,  # 设置界面
        action_type="click",
        wait_time=1000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(step_click_item)
    db.flush()
    steps.append(step_click_item)

    # 步骤4: 验证界面打开成功
    step_verify = Step(
        name="验证界面打开",
        description=f"验证[{item_name}]界面成功打开",
        screen_id=3,  # 具体功能界面
        action_type="assert_exists",
        wait_time=500,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(step_verify)
    db.flush()
    steps.append(step_verify)

    # 步骤5: 返回（后置步骤）
    step_back = Step(
        name="返回上级",
        description="按返回键返回上级界面",
        screen_id=3,
        action_type="hardware_back",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(step_back)
    db.flush()
    steps.append(step_back)

    # 步骤6: 重启应用（后置流程）
    step_restart = Step(
        name="重启应用",
        description="重启应用，准备下一个测试",
        screen_id=1,
        action_type="adb_restart_app",
        action_value="com.chcnav.rtg",  # 应用包名
        wait_time=3000,
        continue_on_error=True,  # 即使失败也继续
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(step_restart)
    db.flush()
    steps.append(step_restart)

    # 将步骤添加到测试用例
    for order, step in enumerate(steps):
        testcase_item = TestcaseItem(
            testcase_id=testcase.id,
            item_type='step',
            step_id=step.id,
            order_index=order,
        )
        db.add(testcase_item)

    db.flush()
    return testcase


if __name__ == '__main__':
    create_test_plan()
