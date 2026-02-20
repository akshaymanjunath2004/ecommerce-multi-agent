from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from shared.config.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth_schema"}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())