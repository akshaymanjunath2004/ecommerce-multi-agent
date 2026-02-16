from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from shared.config.database import get_db
from .schemas import ProductCreate, ProductResponse, StockUpdate
from .service import ProductService

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"service": "product", "status": "running"}


@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    return await ProductService.create_product(db, product)

@router.get("/", response_model=list[ProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db)
):
    return await ProductService.list_products(db)

@router.post("/{product_id}/reduce_stock", response_model=ProductResponse)
async def reduce_stock(
    product_id: int,
    update: StockUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await ProductService.reduce_stock(db, product_id, update.quantity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/reset_db")
async def reset_db(db: AsyncSession = Depends(get_db)):
    """Deletes all products. FOR TESTING ONLY."""
    await db.execute(text("TRUNCATE TABLE product_schema.products RESTART IDENTITY CASCADE"))
    await db.commit()
    return {"status": "cleared"}

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    product = await ProductService.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product