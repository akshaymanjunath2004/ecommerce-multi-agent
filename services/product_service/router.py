from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from services.product_service.repository import ProductRepository
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

@staticmethod
async def reduce_stock(db: AsyncSession, product_id: int, quantity: int):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    product = await ProductRepository.get_product_by_id(db, product_id)

    if not product:
        raise ValueError("Product not found.")

    if product.stock < quantity:
        raise ValueError("Insufficient stock.")

    product.stock -= quantity
    return await ProductRepository.update_product(db, product)

    
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