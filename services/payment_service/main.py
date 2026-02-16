from fastapi import FastAPI
from sqlalchemy import text
from shared.config.database import engine, Base
from .router import router
from .models import Payment

payment_app = FastAPI(title="Payment Service", version="1.0.0")

payment_app.include_router(router)

@payment_app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS payment_schema"))
        await conn.run_sync(Base.metadata.create_all)