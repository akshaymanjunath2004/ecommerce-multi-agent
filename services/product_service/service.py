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

    @staticmethod
    async def reduce_stock(db: AsyncSession, product_id: int, quantity: int):
        # 1. Get Product
        product = await ProductRepository.get_product_by_id(db, product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # 2. Check Stock
        if product.stock < quantity:
            raise ValueError(f"Insufficient stock for Product {product.name}")

        # 3. Deduct
        product.stock -= quantity
        return await ProductRepository.update_product(db, product)
    
    @staticmethod
    async def get_product_by_id(db: AsyncSession, product_id: int):
        return await ProductRepository.get_product_by_id(db, product_id)
    
    @staticmethod
    async def restore_stock(db: AsyncSession, product_id: int, quantity: int):
        return await ProductRepository.restore_stock(db, product_id, quantity)