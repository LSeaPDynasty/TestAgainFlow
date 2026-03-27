"""
TestcaseItem Repository
"""
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.testcase_item import TestcaseItem
from app.models.testcase import Testcase


class TestcaseItemRepository:
    """TestcaseItem repository"""

    def __init__(self, db: Session):
        self.db = db

    def get_items_by_testcase(self, testcase_id: int) -> List[TestcaseItem]:
        """Get all items for a testcase, ordered by order_index"""
        return self.db.query(TestcaseItem).filter(
            TestcaseItem.testcase_id == testcase_id
        ).order_by(TestcaseItem.order_index).all()

    def get_items_with_details(self, testcase_id: int) -> List[dict]:
        """
        Get items with expanded flow/step details

        Returns a list of dicts with flow_name, step_name, step_action_type etc.
        """
        from app.models.flow import Flow
        from app.models.step import Step

        items = self.get_items_by_testcase(testcase_id)

        result = []
        for item in items:
            item_dict = {
                "id": item.id,
                "testcase_id": item.testcase_id,
                "item_type": item.item_type,
                "flow_id": item.flow_id,
                "step_id": item.step_id,
                "order_index": item.order_index,
                "enabled": item.enabled,
                "continue_on_error": item.continue_on_error,
                "params": item.params,
                "created_at": item.created_at,
                "updated_at": item.updated_at,
            }

            # Expand flow
            if item.item_type == 'flow' and item.flow_id:
                flow = self.db.query(Flow).filter_by(id=item.flow_id).first()
                if flow:
                    item_dict["flow_name"] = flow.name
                    item_dict["flow_description"] = flow.description

            # Expand step
            if item.item_type == 'step' and item.step_id:
                step = self.db.query(Step).filter_by(id=item.step_id).first()
                if step:
                    item_dict["step_name"] = step.name
                    item_dict["step_action_type"] = step.action_type
                    item_dict["step_description"] = step.description

            result.append(item_dict)

        return result

    def replace_items(
        self,
        testcase_id: int,
        items_data: List[dict]
    ) -> List[TestcaseItem]:
        """
        Replace all items for a testcase

        Deletes all existing items and creates new ones.
        Returns the created items.
        """
        # Delete existing items
        self.db.query(TestcaseItem).filter(
            TestcaseItem.testcase_id == testcase_id
        ).delete()

        # Create new items
        created_items = []
        for item_data in items_data:
            item = TestcaseItem(
                testcase_id=testcase_id,
                item_type=item_data['item_type'],
                flow_id=item_data.get('flow_id'),
                step_id=item_data.get('step_id'),
                order_index=item_data['order_index'],
                enabled=item_data.get('enabled', True),
                continue_on_error=item_data.get('continue_on_error'),
                params=item_data.get('params')
            )
            self.db.add(item)
            created_items.append(item)

        self.db.commit()

        # Refresh to get IDs
        for item in created_items:
            self.db.refresh(item)

        return created_items

    def create_item(
        self,
        testcase_id: int,
        item_data: dict
    ) -> TestcaseItem:
        """Create a single testcase item"""
        item = TestcaseItem(
            testcase_id=testcase_id,
            item_type=item_data['item_type'],
            flow_id=item_data.get('flow_id'),
            step_id=item_data.get('step_id'),
            order_index=item_data['order_index'],
            enabled=item_data.get('enabled', True),
            continue_on_error=item_data.get('continue_on_error'),
            params=item_data.get('params')
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_item(
        self,
        item_id: int,
        item_data: dict
    ) -> Optional[TestcaseItem]:
        """Update a testcase item"""
        item = self.db.query(TestcaseItem).filter_by(id=item_id).first()
        if not item:
            return None

        for key, value in item_data.items():
            if hasattr(item, key):
                setattr(item, key, value)

        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_item(self, item_id: int) -> bool:
        """Delete a testcase item"""
        item = self.db.query(TestcaseItem).filter_by(id=item_id).first()
        if not item:
            return False

        self.db.delete(item)
        self.db.commit()
        return True

    def delete_all_items(self, testcase_id: int) -> int:
        """Delete all items for a testcase, returns count"""
        count = self.db.query(TestcaseItem).filter(
            TestcaseItem.testcase_id == testcase_id
        ).delete()
        self.db.commit()
        return count

    def has_items(self, testcase_id: int) -> bool:
        """Check if testcase has any items"""
        return self.db.query(TestcaseItem).filter(
            TestcaseItem.testcase_id == testcase_id
        ).first() is not None
