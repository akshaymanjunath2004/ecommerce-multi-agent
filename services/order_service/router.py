from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from shared.config.database import get_db
from .schemas import OrderCreate, OrderResponse
from .service import OrderService

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"service": "order", "status": "running"}

@router.post("/", response_model=OrderResponse)
async def create_order(order: OrderCreate, db: AsyncSession = Depends(get_db)):
    return await OrderService.create_order(db, order)

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order