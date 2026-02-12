from sqlalchemy import Column, Integer, String, Float
from shared.config.database import Base
import builtins

class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "product_schema"}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)

print("MODEL BASE ID:", builtins.id(Base))
