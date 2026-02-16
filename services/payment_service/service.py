from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from .models import Payment
from .repository import PaymentRepository
from .schemas import PaymentCreate

class PaymentService:
    @staticmethod
    async def process_payment(db: AsyncSession, data: PaymentCreate):
        # Simulate payment processing logic
        payment = Payment(
            order_id=data.order_id,
            amount=data.amount,
            status="success",
            transaction_id=str(uuid.uuid4())
        )
        return await PaymentRepository.create_payment(db, payment)