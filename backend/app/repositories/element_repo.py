"""
Element repository
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, func
from app.models.element import Element, Locator
from app.models.screen import Screen
from app.repositories.base import BaseRepository


class ElementRepository(BaseRepository[Element]):
    """Element repository"""

    def __init__(self, db: Session):
        super().__init__(Element, db)

    def get_by_name_in_screen(self, name: str, screen_id: int) -> Optional[Element]:
        """Get element by name within a screen"""
        stmt = select(Element).where(
            and_(Element.name == name, Element.screen_id == screen_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_with_locators(self, element_id: int) -> Optional[Element]:
        """Get element with locators loaded"""
        stmt = select(Element).options(joinedload(Element.locators)).where(Element.id == element_id)
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list_by_screen(self, screen_id: int) -> List[Element]:
        """List all elements in a screen"""
        return self.list(filters={'screen_id': screen_id}, limit=1000)

    def count_by_screen(self, screen_id: int) -> int:
        """Count elements in a screen"""
        return self.count(filters={'screen_id': screen_id})

    def list_with_details(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        screen_id: Optional[int] = None,
        locator_type: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List elements with screen and locator info"""
        # Build query with JOIN to load locators in one query
        stmt = select(Element).options(
            joinedload(Element.locators)  # ✅ Eager load locators
        ).join(
            Screen, Screen.id == Element.screen_id
        )

        # Apply filters
        filters = []
        if search:
            filters.append(Element.name.ilike(f'%{search}%'))
        if screen_id:
            filters.append(Element.screen_id == screen_id)
        if locator_type:
            # Subquery to check locator type
            subq = select(Locator.element_id).where(Locator.type == locator_type)
            filters.append(Element.id.in_(subq))

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get total count
        count_stmt = select(func.count(func.distinct(Element.id))).select_from(Element)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total = self.db.execute(count_stmt).scalar() or 0

        # Apply pagination and ordering
        stmt = stmt.order_by(Element.created_at.desc()).offset(skip).limit(limit)

        # Execute query - ✅ Only ONE query with JOIN
        elements = self.db.execute(stmt).unique().scalars().all()

        # Build results
        results = []
        for element in elements:
            results.append({
                'id': element.id,
                'name': element.name,
                'description': element.description,
                'screen_id': element.screen_id,
                'screen_name': element.screen.name if element.screen else None,
                'locators': [
                    {'id': loc.id, 'type': loc.type, 'value': loc.value, 'priority': loc.priority}
                    for loc in element.locators
                ],
                'created_at': element.created_at,
                'updated_at': element.updated_at
            })

        return results, total

    def check_step_usage(self, element_id: int) -> int:
        """Check how many steps use this element"""
        from app.models.step import Step
        stmt = select(func.count(Step.id)).where(Step.element_id == element_id)
        return self.db.execute(stmt).scalar() or 0

    def create_with_locators(self, data: Dict[str, Any]) -> Element:
        """Create element with locators"""
        locators_data = data.pop('locators', [])
        element = Element(**data)
        self.db.add(element)
        self.db.flush()  # Get element ID

        for loc_data in locators_data:
            locator = Locator(element_id=element.id, **loc_data)
            self.db.add(locator)

        self.db.commit()
        self.db.refresh(element)
        return element

    def update_with_locators(self, element_id: int, data: Dict[str, Any]) -> Optional[Element]:
        """Update element with locators"""
        element = self.get(element_id)
        if not element:
            return None

        # Update element fields
        for field, value in data.items():
            if field != 'locators' and hasattr(element, field):
                setattr(element, field, value)

        # Update locators if provided
        if 'locators' in data:
            # Delete existing locators
            self.db.execute(select(Locator).where(Locator.element_id == element_id))
            self.db.query(Locator).filter(Locator.element_id == element_id).delete()

            # Add new locators
            for loc_data in data['locators']:
                locator = Locator(element_id=element_id, **loc_data)
                self.db.add(locator)

        self.db.commit()
        self.db.refresh(element)
        return element
