from fastapi import FastAPI
from sqlalchemy import text
from shared.config.database import engine, Base
from shared.observability import setup_observability
from .router import router, public_router
from .models import Order # Import to register with Base

order_app = FastAPI(title="Order Service", version="1.0.0")

# --- OBSERVABILITY BOOTSTRAP ---
setup_observability(order_app, "order_service")

order_app.include_router(public_router)
order_app.include_router(router)

@order_app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS order_schema"))
        await conn.run_sync(Base.metadata.create_all)