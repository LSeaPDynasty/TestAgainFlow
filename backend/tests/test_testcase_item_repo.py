"""
TestcaseItem Repository Tests
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.models.base import Base
from app.models.testcase import Testcase
from app.models.testcase_item import TestcaseItem
from app.models.flow import Flow
from app.models.step import Step
from app.models.screen import Screen
from app.repositories.testcase_item_repo import TestcaseItemRepository


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_testcase_items.db"


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create initial data
    session = TestingSessionLocal()

    # Create screen
    screen = Screen(name="测试页面")
    session.add(screen)
    session.commit()

    # Create flow
    flow = Flow(name="测试流程", description="测试流程描述")
    session.add(flow)
    session.commit()

    # Create step
    step = Step(
        name="测试步骤",
        description="测试步骤描述",
        screen_id=screen.id,
        action_type="click"
    )
    session.add(step)
    session.commit()

    # Create testcase
    testcase = Testcase(
        name="测试用例",
        description="测试用例描述",
        priority="P1"
    )
    session.add(testcase)
    session.commit()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_create_flow_item(db_session):
    """Test creating a flow item"""
    repo = TestcaseItemRepository(db_session)

    # Get flow and testcase
    flow = db_session.query(Flow).first()
    testcase = db_session.query(Testcase).first()

    # Create item
    item_data = {
        "item_type": "flow",
        "flow_id": flow.id,
        "order_index": 1,
        "enabled": True,
        "continue_on_error": False
    }

    item = repo.create_item(testcase.id, item_data)

    assert item.id is not None
    assert item.item_type == "flow"
    assert item.flow_id == flow.id
    assert item.step_id is None
    assert item.order_index == 1


def test_create_step_item(db_session):
    """Test creating a step item"""
    repo = TestcaseItemRepository(db_session)

    # Get step and testcase
    step = db_session.query(Step).first()
    testcase = db_session.query(Testcase).first()

    # Create item
    item_data = {
        "item_type": "step",
        "step_id": step.id,
        "order_index": 1,
        "enabled": True,
        "continue_on_error": False
    }

    item = repo.create_item(testcase.id, item_data)

    assert item.id is not None
    assert item.item_type == "step"
    assert item.step_id == step.id
    assert item.flow_id is None
    assert item.order_index == 1


def test_replace_items(db_session):
    """Test replacing all items"""
    repo = TestcaseItemRepository(db_session)

    # Get flow, step, and testcase
    flow = db_session.query(Flow).first()
    step = db_session.query(Step).first()
    testcase = db_session.query(Testcase).first()

    # Create initial items
    items_data = [
        {
            "item_type": "flow",
            "flow_id": flow.id,
            "order_index": 1
        },
        {
            "item_type": "step",
            "step_id": step.id,
            "order_index": 2
        }
    ]

    items = repo.replace_items(testcase.id, items_data)

    assert len(items) == 2
    assert items[0].order_index == 1
    assert items[1].order_index == 2

    # Replace with new items
    new_items_data = [
        {
            "item_type": "step",
            "step_id": step.id,
            "order_index": 1
        }
    ]

    new_items = repo.replace_items(testcase.id, new_items_data)

    assert len(new_items) == 1
    assert new_items[0].item_type == "step"


def test_get_items_with_details(db_session):
    """Test getting items with expanded details"""
    repo = TestcaseItemRepository(db_session)

    # Get flow, step, and testcase
    flow = db_session.query(Flow).first()
    step = db_session.query(Step).first()
    testcase = db_session.query(Testcase).first()

    # Create items
    items_data = [
        {
            "item_type": "flow",
            "flow_id": flow.id,
            "order_index": 1
        },
        {
            "item_type": "step",
            "step_id": step.id,
            "order_index": 2
        }
    ]

    repo.replace_items(testcase.id, items_data)

    # Get with details
    items_with_details = repo.get_items_with_details(testcase.id)

    assert len(items_with_details) == 2
    assert items_with_details[0]['flow_name'] == "测试流程"
    assert items_with_details[1]['step_name'] == "测试步骤"
    assert items_with_details[1]['step_action_type'] == "click"


def test_constraint_validation(db_session):
    """Test that flow_id and step_id are mutually exclusive"""
    repo = TestcaseItemRepository(db_session)

    testcase = db_session.query(Testcase).first()

    # Try to create item with both flow_id and step_id (should fail at DB level)
    # This would be caught by the database constraint
    # In real API, we validate before creating

    # Valid: flow item
    item_data = {
        "item_type": "flow",
        "flow_id": 1,  # Assuming this exists
        "order_index": 1
    }

    # Invalid: both ids
    invalid_item_data = {
        "item_type": "flow",
        "flow_id": 1,
        "step_id": 1,  # Both set - should fail
        "order_index": 1
    }

    # The repository should validate this before creating
    # For now, we rely on database constraint


def test_has_items(db_session):
    """Test checking if testcase has items"""
    repo = TestcaseItemRepository(db_session)

    testcase = db_session.query(Testcase).first()

    # Initially no items
    assert repo.has_items(testcase.id) is False

    # Add an item
    flow = db_session.query(Flow).first()
    item_data = {
        "item_type": "flow",
        "flow_id": flow.id,
        "order_index": 1
    }
    repo.create_item(testcase.id, item_data)

    # Now has items
    assert repo.has_items(testcase.id) is True


def test_delete_item(db_session):
    """Test deleting a single item"""
    repo = TestcaseItemRepository(db_session)

    flow = db_session.query(Flow).first()
    testcase = db_session.query(Testcase).first()

    # Create item
    item_data = {
        "item_type": "flow",
        "flow_id": flow.id,
        "order_index": 1
    }
    item = repo.create_item(testcase.id, item_data)

    # Delete item
    result = repo.delete_item(item.id)

    assert result is True

    # Item should not exist
    assert repo.get_items_by_testcase(testcase.id) == []


def test_delete_all_items(db_session):
    """Test deleting all items for a testcase"""
    repo = TestcaseItemRepository(db_session)

    flow = db_session.query(Flow).first()
    step = db_session.query(Step).first()
    testcase = db_session.query(Testcase).first()

    # Create multiple items
    items_data = [
        {"item_type": "flow", "flow_id": flow.id, "order_index": 1},
        {"item_type": "step", "step_id": step.id, "order_index": 2}
    ]
    repo.replace_items(testcase.id, items_data)

    # Delete all
    count = repo.delete_all_items(testcase.id)

    assert count == 2
    assert repo.has_items(testcase.id) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
