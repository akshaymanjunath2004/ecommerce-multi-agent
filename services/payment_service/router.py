from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared.config.database import get_db
from .schemas import PaymentCreate, PaymentResponse
from .service import PaymentService

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"service": "payment", "status": "running"}

@router.post("/", response_model=PaymentResponse)
async def process_payment(payment: PaymentCreate, db: AsyncSession = Depends(get_db)):
    return await PaymentService.process_payment(db, payment)