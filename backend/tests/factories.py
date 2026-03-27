"""
Test data factories - 快速创建测试数据
"""
from sqlalchemy.orm import Session
from app.models.screen import Screen
from app.models.element import Element, Locator
from app.models.step import Step
from app.models.flow import Flow, FlowStep
from app.models.testcase import Testcase, TestcaseFlow
from app.models.profile import Profile
from app.models.device import Device
from app.models.tag import Tag
from app.models.suite import Suite, SuiteTestcase


class TestDataFactory:
    """测试数据工厂类"""

    @staticmethod
    def create_screen(db: Session, **kwargs) -> Screen:
        """创建界面"""
        data = {
            "name": kwargs.get("name", "TestScreen"),
            "activity": kwargs.get("activity", "com.example.TestActivity"),
            "description": kwargs.get("description", "测试界面")
        }
        screen = Screen(**data)
        db.add(screen)
        db.commit()
        db.refresh(screen)
        return screen

    @staticmethod
    def create_element(db: Session, screen_id: int, **kwargs) -> Element:
        """创建元素"""
        data = {
            "name": kwargs.get("name", "testElement"),
            "description": kwargs.get("description", "测试元素"),
            "screen_id": screen_id
        }
        element = Element(**data)
        db.add(element)
        db.flush()

        # 添加定位符
        locators_data = kwargs.get("locators", [
            {"type": "resource-id", "value": "com.app:id/test", "priority": 1}
        ])
        for loc_data in locators_data:
            locator = Locator(element_id=element.id, **loc_data)
            db.add(locator)

        db.commit()
        db.refresh(element)
        return element

    @staticmethod
    def create_step(db: Session, screen_id: int, **kwargs) -> Step:
        """创建步骤"""
        data = {
            "name": kwargs.get("name", "测试步骤"),
            "description": kwargs.get("description", "测试步骤描述"),
            "screen_id": screen_id,
            "action_type": kwargs.get("action_type", "click"),
            "element_id": kwargs.get("element_id"),
            "action_value": kwargs.get("action_value"),
            "wait_after_ms": kwargs.get("wait_after_ms", 0)
        }
        step = Step(**data)
        db.add(step)
        db.commit()
        db.refresh(step)
        return step

    @staticmethod
    def create_flow(db: Session, **kwargs) -> Flow:
        """创建流程"""
        data = {
            "name": kwargs.get("name", "TestFlow"),
            "description": kwargs.get("description", "测试流程"),
            "flow_type": kwargs.get("flow_type", "standard"),
            "requires": kwargs.get("requires"),
            "default_params": kwargs.get("default_params")
        }
        flow = Flow(**data)
        db.add(flow)
        db.flush()

        # 添加步骤
        steps_data = kwargs.get("steps", [])
        for idx, step_data in enumerate(steps_data, start=1):
            flow_step = FlowStep(
                flow_id=flow.id,
                step_id=step_data["step_id"],
                order_index=step_data.get("order", idx)
            )
            db.add(flow_step)

        db.commit()
        db.refresh(flow)
        return flow

    @staticmethod
    def create_testcase(db: Session, **kwargs) -> Testcase:
        """创建用例"""
        data = {
            "name": kwargs.get("name", "TestCase"),
            "description": kwargs.get("description", "测试用例"),
            "priority": kwargs.get("priority", "P2"),
            "timeout": kwargs.get("timeout", 120),
            "params": kwargs.get("params")
        }
        testcase = Testcase(**data)
        db.add(testcase)
        db.flush()

        # 添加流程
        flows_data = kwargs.get("main_flows", [])
        for idx, flow_data in enumerate(flows_data, start=1):
            tc_flow = TestcaseFlow(
                testcase_id=testcase.id,
                flow_id=flow_data["flow_id"],
                flow_role="main",
                order_index=flow_data.get("order", idx),
                enabled=flow_data.get("enabled", True),
                params=flow_data.get("params")
            )
            db.add(tc_flow)

        db.commit()
        db.refresh(testcase)
        return testcase

    @staticmethod
    def create_profile(db: Session, **kwargs) -> Profile:
        """创建 Profile"""
        data = {
            "name": kwargs.get("name", "test_profile"),
            "description": kwargs.get("description", "测试配置"),
            "variables": kwargs.get("variables", {})
        }
        profile = Profile(**data)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def create_device(db: Session, **kwargs) -> Device:
        """创建设备"""
        data = {
            "name": kwargs.get("name", "TestDevice"),
            "serial": kwargs.get("serial", "test_serial_001"),
            "model": kwargs.get("model", "TestModel"),
            "os_version": kwargs.get("os_version", "Android 12"),
            "connection_type": kwargs.get("connection_type", "usb"),
            "capabilities": kwargs.get("capabilities")
        }
        device = Device(**data)
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def create_tag(db: Session, **kwargs) -> Tag:
        """创建标签"""
        data = {
            "name": kwargs.get("name", "test_tag"),
            "color": kwargs.get("color", "#00ff00")
        }
        tag = Tag(**data)
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag

    @staticmethod
    def create_suite(db: Session, **kwargs) -> Suite:
        """创建套件"""
        data = {
            "name": kwargs.get("name", "TestSuite"),
            "description": kwargs.get("description", "测试套件"),
            "enabled": kwargs.get("enabled", True)
        }
        suite = Suite(**data)
        db.add(suite)
        db.flush()

        # 添加用例
        testcase_ids = kwargs.get("testcase_ids", [])
        for idx, tc_id in enumerate(testcase_ids, start=1):
            from app.models.suite import SuiteTestcase
            suite_tc = SuiteTestcase(
                suite_id=suite.id,
                testcase_id=tc_id,
                order_index=idx
            )
            db.add(suite_tc)

        db.commit()
        db.refresh(suite)
        return suite
