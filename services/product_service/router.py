from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared.config.database import get_db
from .schemas import ProductCreate, ProductResponse
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