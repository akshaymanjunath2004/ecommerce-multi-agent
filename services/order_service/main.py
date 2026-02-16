from fastapi import FastAPI
from sqlalchemy import text
from shared.config.database import engine, Base
from .router import router
from .models import Order # Import to register with Base

order_app = FastAPI(title="Order Service", version="1.0.0")

order_app.include_router(router)

@order_app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS order_schema"))
        await conn.run_sync(Base.metadata.create_all)