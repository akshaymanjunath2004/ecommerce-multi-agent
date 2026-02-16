from sqlalchemy.ext.asyncio import AsyncSession
from .models import Payment

class PaymentRepository:
    @staticmethod
    async def create_payment(db: AsyncSession, payment: Payment):
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        return payment