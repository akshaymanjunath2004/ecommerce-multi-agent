from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from services.product_service.repository import ProductRepository
from shared.config.database import get_db
from shared.security.dependencies import verify_internal_api_key
from .schemas import ProductCreate, ProductResponse, StockUpdate
from .service import ProductService

router = APIRouter(dependencies=[Depends(verify_internal_api_key)])
public_router = APIRouter()  # For any public endpoints (e.g. health check)

@public_router.get("/health")
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
    query: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    products = await ProductService.list_products(db)

    if query:
        query_words = set(query.lower().split())
        filtered = []

        for p in products:
            name_words = set(p.name.lower().split())
            if query_words & name_words:
                filtered.append(p)

        products = filtered

    return products

# FIX: Added proper route decorator and used Pydantic model for body
@router.post("/{product_id}/reduce_stock")
async def reduce_stock(
    product_id: int,
    stock_update: StockUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await ProductService.reduce_stock(db, product_id, stock_update.quantity)
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

@router.post("/{product_id}/restore_stock")
async def restore_stock(product_id: int, payload: StockUpdate, db: AsyncSession = Depends(get_db)):
    success = await ProductService.restore_stock(db, product_id, payload.quantity)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Stock restored"}