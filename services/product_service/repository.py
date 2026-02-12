from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Product

class ProductRepository:

    @staticmethod
    async def create_product(db: AsyncSession, product: Product):
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def get_all_products(db: AsyncSession):
        result = await db.execute(select(Product))
        return result.scalars().all()
