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

    @staticmethod
    async def get_product_by_id(db: AsyncSession, product_id: int):
        result = await db.execute(select(Product).where(Product.id == product_id))
        return result.scalars().first()

    @staticmethod
    async def update_product(db: AsyncSession, product: Product):
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product