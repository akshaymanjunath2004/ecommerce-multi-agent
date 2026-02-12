from fastapi import FastAPI
from .router import router
from sqlalchemy import text
from shared.config.database import engine, Base
import builtins
from .models import Product

product_app = FastAPI(
    title="Product Service",
    version="1.0.0"
)

product_app.include_router(router)

@product_app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        # Create schema if not exists
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS product_schema"))
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    print("TABLES:", Base.metadata.tables.keys())
    print(Base.metadata.tables)
    print(Base.metadata.tables.keys())
    print("STARTUP BASE ID:", builtins.id(Base))
    print("METADATA TABLES:", Base.metadata.tables.keys())