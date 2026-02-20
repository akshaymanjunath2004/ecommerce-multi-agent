from sqlalchemy.ext.asyncio import AsyncSession
from .models import Order
from .repository import OrderRepository
from .schemas import OrderCreate

class OrderService:
    @staticmethod
    async def create_order(db: AsyncSession, data: OrderCreate):
        total = data.unit_price * data.quantity
        order = Order(
            product_id=data.product_id,
            quantity=data.quantity,
            total_price=total,
            status="pending"
        )
        if data.quantity<=0:
            raise ValueError("Invalid Quantity.")
        
        return await OrderRepository.create_order(db, order)

    @staticmethod
    async def get_order(db: AsyncSession, order_id: int):
        return await OrderRepository.get_order(db, order_id)
    
    @staticmethod
    async def cancel_order(db: AsyncSession, order_id: int):
        return await OrderRepository.cancel_order(db, order_id)