"""
FIX GAP #5: Payment endpoints now require X-Internal-API-Key.
Previously anyone could POST /payment/ and generate arbitrary payment
records in the database without going through checkout.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config.database import get_db
from shared.security.dependencies import verify_internal_api_key

from .schemas import PaymentCreate, PaymentResponse
from .service import PaymentService

# FIX GAP #5: Router-level dependency protects all payment endpoints
router = APIRouter(dependencies=[Depends(verify_internal_api_key)])
public_router = APIRouter()  # For any public endpoints (e.g. health check)

@public_router.get("/health", include_in_schema=False)
async def health_check():
    return {"service": "payment", "status": "running"}


@router.post("/", response_model=PaymentResponse)
async def process_payment(
    payment: PaymentCreate, db: AsyncSession = Depends(get_db)
):
    return await PaymentService.process_payment(db, payment)