from sqlalchemy import Column, Integer, String, Float
from shared.config.database import Base

class Order(Base):
    __tablename__ = "orders"
    # We use a separate schema to simulate microservice isolation
    __table_args__ = {"schema": "order_schema"}

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False) # calculated at creation
    status = Column(String, default="pending") # pending, paid, shipped