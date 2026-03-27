"""User model."""
from sqlalchemy import Boolean, Column, String

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False, default="member")
    is_active = Column(Boolean, nullable=False, default=True)
