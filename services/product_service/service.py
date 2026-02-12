from sqlalchemy.ext.asyncio import AsyncSession
from .models import Product
from .repository import ProductRepository
from .schemas import ProductCreate

class ProductService:

    @staticmethod
    async def create_product(db: AsyncSession, data: ProductCreate):
        product = Product(
            name=data.name,
            price=data.price,
            stock=data.stock
        )
        return await ProductRepository.create_product(db, product)

    @staticmethod
    async def list_products(db: AsyncSession):
        return await ProductRepository.get_all_products(db)
