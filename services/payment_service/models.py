from sqlalchemy import Column, Integer, String, Float
from shared.config.database import Base

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = {"schema": "payment_schema"}

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="pending") # pending, success, failed
    transaction_id = Column(String, nullable=True)