from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from shared.config.database import Base

class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = {"schema": "session_schema"}

    session_id = Column(String, primary_key=True, index=True) # UUID string
    user_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationship to items
    items = relationship("SessionItem", back_populates="session", lazy="selectin")

class SessionItem(Base):
    __tablename__ = "session_items"
    __table_args__ = {"schema": "session_schema"}

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("session_schema.sessions.session_id"))
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)

    session = relationship("Session", back_populates="items")