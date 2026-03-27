"""
TestFlow Backend - Test Suite Configuration

pytest.ini:
    [pytest]
    testpaths = tests
    python_files = test_*.py
    python_classes = Test*
    addopts =
        -v
        --strict-markers
        --tb=short
        --disable-warnings
"""
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.models import Base


# 使用内存SQLite进行测试
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def db() -> Generator[Session, None, None]:
    """
    创建测试数据库会话

    每个测试函数都会：
    1. 创建所有表
    2. 提供数据库会话
    3. 测试结束后回滚事务并删除表
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建会话
    session = TestingSessionLocal()

    yield session

    # 清理
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function", autouse=True)
def mock_adb_functions(monkeypatch):
    """自动 mock ADB 函数，避免真实设备连接"""
    # Mock device online check
    monkeypatch.setattr(
        "app.utils.adb.check_device_online",
        lambda serial: True  # Always return online
    )
    # Mock get_adb_devices
    monkeypatch.setattr(
        "app.utils.adb.get_adb_devices",
        lambda: []
    )


@pytest.fixture(scope="function")
def client(db: Session) -> TestClient:
    """
    创建测试客户端

    自动注入测试数据库会话
    """
    from app.dependencies import get_db_session

    def override_get_db():
        yield db

    app.dependency_overrides[get_db_session] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# 基础数据 fixtures
@pytest.fixture
def screen(db: Session):
    """预建界面记录"""
    from app.models.screen import Screen
    screen = Screen(
        name="LoginPage",
        activity="com.example.app.LoginActivity",
        description="登录界面"
    )
    db.add(screen)
    db.commit()
    db.refresh(screen)
    return screen


@pytest.fixture
def element(db: Session, screen):
    """预建元素记录"""
    from app.models.element import Element, Locator
    element = Element(
        name="loginBtn",
        description="登录按钮",
        screen_id=screen.id
    )
    db.add(element)
    db.flush()

    locator = Locator(
        element_id=element.id,
        type="resource-id",
        value="com.app:id/login_btn",
        priority=1
    )
    db.add(locator)
    db.commit()
    db.refresh(element)
    return element


@pytest.fixture
def step(db: Session, screen, element):
    """预建步骤记录"""
    from app.models.step import Step
    step = Step(
        name="点击登录按钮",
        description="在登录页点击登录按钮",
        screen_id=screen.id,
        action_type="click",
        element_id=element.id
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    return step


@pytest.fixture
def flow(db: Session, step):
    """预建流程记录"""
    from app.models.flow import Flow, FlowStep
    flow = Flow(
        name="LoginFlow",
        description="登录流程",
        flow_type="standard"
    )
    db.add(flow)
    db.flush()

    flow_step = FlowStep(
        flow_id=flow.id,
        step_id=step.id,
        order_index=1
    )
    db.add(flow_step)
    db.commit()
    db.refresh(flow)
    return flow


@pytest.fixture
def testcase(db: Session, flow):
    """预建用例记录"""
    from app.models.testcase import Testcase, TestcaseFlow
    testcase = Testcase(
        name="LoginTest",
        description="验证登录功能",
        priority="P1",
        timeout=120
    )
    db.add(testcase)
    db.flush()

    tc_flow = TestcaseFlow(
        testcase_id=testcase.id,
        flow_id=flow.id,
        flow_role="main",
        order_index=1,
        enabled=True
    )
    db.add(tc_flow)
    db.commit()
    db.refresh(testcase)
    return testcase


@pytest.fixture
def profile(db: Session):
    """预建 Profile 记录"""
    from app.models.profile import Profile
    profile = Profile(
        name="staging",
        description="测试环境",
        variables={
            "base_url": "https://staging.example.com",
            "username": "test_user"
        }
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def device(db: Session):
    """预建设备记录"""
    from app.models.device import Device
    device = Device(
        name="小米11",
        serial="abc123def456",
        model="21091116C",
        os_version="Android 12",
        connection_type="usb",
        capabilities={
            "biometric": True,
            "nfc": False,
            "camera": True
        }
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@pytest.fixture
def tag(db: Session):
    """预建标签记录"""
    from app.models.tag import Tag
    tag = Tag(
        name="smoke",
        color="#ff0000"
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@pytest.fixture
def project(db: Session):
    """预建项目记录"""
    from app.models.project import Project
    project = Project(
        name="TestProject",
        description="Test project",
        status="active",
        priority="P1"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def suite(db: Session):
    """预建套件记录"""
    from app.models.suite import Suite, SuiteTestcase
    suite = Suite(
        name="LoginSuite",
        description="登录测试套件",
        enabled=True
    )
    db.add(suite)
    db.commit()
    db.refresh(suite)
    return suite


# Mock fixtures
@pytest.fixture
def mock_adb_devices(monkeypatch):
    """Mock ADB 设备列表"""
    monkeypatch.setattr(
        "app.utils.adb.get_adb_devices",
        lambda: [
            {
                "serial": "abc123def456",
                "status": "device",
                "model": "21091116C"
            }
        ]
    )


@pytest.fixture
def mock_adb_check_online(monkeypatch):
    """Mock ADB 设备在线检查"""
    monkeypatch.setattr(
        "app.utils.adb.check_device_online",
        lambda serial: serial == "abc123def456"
    )


@pytest.fixture
def mock_adb_find_element(monkeypatch):
    """Mock ADB 元素查找"""
    monkeypatch.setattr(
        "app.utils.adb.find_element",
        lambda serial, ltype, lvalue: {
            "found": True,
            "locator_type": ltype,
            "locator_value": lvalue,
            "bounds": {"left": 100, "top": 200, "right": 300, "bottom": 250}
        }
    )
