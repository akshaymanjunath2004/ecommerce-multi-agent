from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Order

class OrderRepository:
    @staticmethod
    async def create_order(db: AsyncSession, order: Order):
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def get_order(db: AsyncSession, order_id: int):
        result = await db.execute(select(Order).where(Order.id == order_id))
        return result.scalars().first()
    
    @staticmethod
    async def cancel_order(db: AsyncSession, order_id: int):
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalars().first()
        
        if not order:
            return None
            
        order.status = "cancelled"
        
        await db.commit()
        await db.refresh(order)
        return order