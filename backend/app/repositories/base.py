"""
Base repository - common CRUD operations
"""
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, delete
from app.models.base import BaseModel

ModelType = TypeVar('ModelType', bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: int) -> Optional[ModelType]:
        """Get by ID"""
        return self.db.get(self.model, id)

    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """Get by field value"""
        stmt = select(self.model).where(getattr(self.model, field) == value)
        return self.db.execute(stmt).scalar_one_or_none()

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order: str = 'desc'
    ) -> List[ModelType]:
        """List with pagination and filters"""
        stmt = select(self.model)

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    if isinstance(value, str) and key in ['name', 'description']:
                        # Text search for string fields
                        stmt = stmt.where(getattr(self.model, key).ilike(f'%{value}%'))
                    else:
                        stmt = stmt.where(getattr(self.model, key) == value)

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            stmt = stmt.order_by(order_field.desc() if order == 'desc' else order_field.asc())

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        return list(self.db.execute(stmt).scalars().all())

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters"""
        stmt = select(func.count(self.model.id))

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    if isinstance(value, str) and key in ['name', 'description']:
                        stmt = stmt.where(getattr(self.model, key).ilike(f'%{value}%'))
                    else:
                        stmt = stmt.where(getattr(self.model, key) == value)

        return self.db.execute(stmt).scalar() or 0

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create new record"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: int, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """Update record"""
        db_obj = self.get(id)
        if not db_obj:
            return None

        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """Delete record"""
        db_obj = self.get(id)
        if not db_obj:
            return False

        self.db.delete(db_obj)
        self.db.commit()
        return True

    def exists(self, filters: Dict[str, Any]) -> bool:
        """Check if record exists"""
        stmt = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        return self.db.execute(stmt.limit(1)).scalar_one_or_none() is not None

    def bulk_create(self, items: List[Dict[str, Any]]) -> List[ModelType]:
        """Bulk create records"""
        db_objs = [self.model(**item) for item in items]
        self.db.add_all(db_objs)
        self.db.commit()
        for obj in db_objs:
            self.db.refresh(obj)
        return db_objs
