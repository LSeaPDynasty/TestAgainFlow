# -*- coding: utf-8 -*-
"""
创建完整的设置界面测试计划（包含步骤、元素、测试用例）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.project import Project
from app.models.suite import Suite, SuiteTestcase
from app.models.testcase import Testcase
from app.models.testcase_item import TestcaseItem
from app.models.step import Step
from app.models.test_plan import TestPlan, TestPlanSuite
from datetime import datetime

# 设置界面功能项映射（元素名称 -> 测试用例名称）
SETTINGS_ITEMS = {
    # 作业管理
    'projectManagementButton': '项目管理',
    'coordinateSystemButton': '坐标系统',
    'pointCalibrationButton': '点校正',
    'baseStationTranslationButton': '基线计算',
    'pointManagementButton': '记录点库',

    # 数据采集
    'propertyLibraryButton': '属性定义',
    'vehicleLibraryButton': '代码定义',

    # 仪器设置
    'rtkConfigurationButton': 'RTK配置',
    'radioInformationButton': '电台信息',
    'deviceManagementButton': '设备管理',

    # 网络/设备
    'measurementRtkButton': '测量RTK',
    'deviceCodeButton': '设备编码',
    'hotSpotInformationButton': '热点信息',
    'wifiCameraButton': 'WiFi摄像头',

    # 存储/文件
    'fileManagementButton': '文件管理',
    'drawingButton': '图纸管理',
    'logButton': '日志管理',

    # 显示设置
    'mapButton': '地图设置',
    'nightModeButton': '夜间模式',
    'unitSettingButton': '单位设置',
    'languageSettingButton': '语言设置',
    'soundSettingButton': '声音设置',

    # 其他设置
    'versionInformationButton': '版本信息',
    'sceneInformationButton': '场景信息',
    'skyMapButton': '天图',
    'faultDetectionButton': '故障检测',
    'demonstrationModeButton': '演示模式',
    'clearCacheButton': '清除缓存',
    'softwareRegistrationCodeButton': '软件注册码',
    'developerCenterButton': '开发者中心',
    'systemManagementButton': '系统管理',
}


def create_complete_test_plan():
    """创建完整的测试计划（包含步骤）"""
    db = SessionLocal()
    try:
        # 获取项目
        project = db.query(Project).filter(Project.id == 1).first()
        if not project:
            print("Error: Project ID 1 not found!")
            return

        # 获取界面ID
        main_screen = db.query(Screen).filter(Screen.id == 1).first()
        settings_screen = db.query(Screen).filter(Screen.name == 'SettingsPage').first()

        if not main_screen or not settings_screen:
            print("Error: Required screens not found!")
            return

        print(f"Main screen: {main_screen.name} (ID: {main_screen.id})")
        print(f"Settings screen: {settings_screen.name} (ID: {settings_screen.id})")

        # 查找设置按钮元素
        settings_button = db.query(Element).filter(
            Element.screen_id == main_screen.id,
            Element.name == '首页-设置'
        ).first()

        if not settings_button:
            print("Error: Settings button not found!")
            return

        print(f"Settings button: {settings_button.name} (ID: {settings_button.id})")

        # 删除旧的测试计划（如果存在）
        old_test_plan = db.query(TestPlan).filter(
            TestPlan.name == "设置界面功能测试计划（完整版）"
        ).first()

        if old_test_plan:
            print(f"\n删除旧的测试计划: {old_test_plan.name} (ID: {old_test_plan.id})")
            db.delete(old_test_plan)
            db.flush()

        # 删除旧的套件（如果存在）
        old_suite = db.query(Suite).filter(
            Suite.name == "设置界面功能测试"
        ).first()

        if old_suite:
            print(f"删除旧的套件: {old_suite.name} (ID: {old_suite.id})")

            # 先删除关联的测试用例
            old_suite_testcases = db.query(SuiteTestcase).filter(
                SuiteTestcase.suite_id == old_suite.id
            ).all()

            for st in old_suite_testcases:
                # 删除测试用例的步骤关联
                db.query(TestcaseItem).filter(
                    TestcaseItem.testcase_id == st.testcase_id
                ).delete()
                # 删除测试用例
                db.query(Testcase).filter(
                    Testcase.id == st.testcase_id
                ).delete()

            # 删除套件测试用例关联
            db.query(SuiteTestcase).filter(
                SuiteTestcase.suite_id == old_suite.id
            ).delete()

            # 删除套件
            db.delete(old_suite)
            db.flush()

        # 1. 创建测试计划
        test_plan = TestPlan(
            name="设置界面功能测试计划（完整版）",
            description="测试设置界面下所有功能模块，验证每个功能入口可以正常打开。包含完整测试步骤。",
            execution_strategy="sequential",
            max_parallel_tasks=1,
            enabled=True,
            project_id=project.id,
        )
        db.add(test_plan)
        db.flush()
        print(f"\n{'='*60}")
        print(f"Created test plan: {test_plan.name} (ID: {test_plan.id})")
        print(f"{'='*60}")

        # 2. 创建主套件
        suite = Suite(
            name="设置界面功能测试",
            description="测试设置界面中所有功能项",
            project_id=project.id,
        )
        db.add(suite)
        db.flush()
        print(f"\nCreated suite: {suite.name} (ID: {suite.id})")

        # 将套件添加到测试计划
        test_plan_suite = TestPlanSuite(
            test_plan_id=test_plan.id,
            suite_id=suite.id,
            order_index=0,
            enabled=True,
        )
        db.add(test_plan_suite)

        # 3. 为每个功能项创建测试用例和步骤
        total_testcases = 0

        for element_name, item_display_name in SETTINGS_ITEMS.items():
            # 查找对应的元素
            element = db.query(Element).filter(
                Element.screen_id == settings_screen.id,
                Element.name == element_name
            ).first()

            if not element:
                print(f"  Warning: Element {element_name} not found, skipping...")
                continue

            # 创建测试用例
            testcase = Testcase(
                name=f"设置-{item_display_name}",
                description=f"验证设置界面的[{item_display_name}]功能可以正常打开",
                project_id=project.id,
            )
            db.add(testcase)
            db.flush()
            total_testcases += 1

            # 关联测试用例到套件
            suite_testcase = SuiteTestcase(
                suite_id=suite.id,
                testcase_id=testcase.id,
                order_index=total_testcases - 1,
                enabled=True,
            )
            db.add(suite_testcase)

            # 创建测试步骤
            steps = create_testcase_steps(
                db, main_screen.id, settings_screen.id,
                settings_button.id, element.id, item_display_name
            )

            # 将步骤添加到测试用例
            for order, step in enumerate(steps):
                testcase_item = TestcaseItem(
                    testcase_id=testcase.id,
                    item_type='step',
                    step_id=step.id,
                    order_index=order,
                )
                db.add(testcase_item)

            print(f"  [{total_testcases}] Created testcase: {testcase.name} (ID: {testcase.id}, Element: {element.name})")

        db.commit()
        print(f"\n{'='*60}")
        print(f"测试计划创建完成！")
        print(f"{'='*60}")
        print(f"测试计划: {test_plan.name} (ID: {test_plan.id})")
        print(f"套件: {suite.name} (ID: {suite.id})")
        print(f"测试用例数: {total_testcases}")
        print(f"{'='*60}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def create_testcase_steps(db, main_screen_id, settings_screen_id,
                         settings_button_id, target_element_id, item_name):
    """创建测试用例的步骤"""
    steps = []

    # 步骤1: 启动应用（前置步骤）
    step1 = Step(
        name="启动应用",
        description="启动被测应用",
        screen_id=main_screen_id,
        action_type="adb_start_app",
        action_value="com.chcnav.rtg",
        wait_after_ms=3000,
    )
    db.add(step1)
    db.flush()
    steps.append(step1)

    # 步骤2: 点击设置按钮
    step2 = Step(
        name="点击设置按钮",
        description="进入设置界面",
        screen_id=main_screen_id,
        element_id=settings_button_id,
        action_type="click",
        wait_after_ms=1000,
    )
    db.add(step2)
    db.flush()
    steps.append(step2)

    # 步骤3: 点击目标功能项
    step3 = Step(
        name=f"点击{item_name}",
        description=f"在设置界面点击[{item_name}]功能项",
        screen_id=settings_screen_id,
        element_id=target_element_id,
        action_type="click",
        wait_after_ms=1000,
    )
    db.add(step3)
    db.flush()
    steps.append(step3)

    # 步骤4: 返回
    step4 = Step(
        name="返回上级",
        description="按返回键返回设置界面",
        screen_id=settings_screen_id,
        action_type="hardware_back",
        wait_after_ms=500,
    )
    db.add(step4)
    db.flush()
    steps.append(step4)

    return steps


if __name__ == '__main__':
    # 导入必要的模型
    from app.models.screen import Screen
    from app.models.element import Element

    create_complete_test_plan()
