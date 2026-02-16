from fastapi import FastAPI
from sqlalchemy import text
from shared.config.database import engine, Base
from .router import router
from .models import Session # Important: Import models so Alembic/SQLAlchemy sees them

session_app = FastAPI(title="Session Service", version="1.0.0")

session_app.include_router(router)

@session_app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS session_schema"))
        await conn.run_sync(Base.metadata.create_all)