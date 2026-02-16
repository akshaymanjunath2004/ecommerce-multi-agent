from fastapi import FastAPI
from sqlalchemy import text
from shared.config.database import engine, Base

# IMPORTANT: import models so they register with Base
from services.product_service import models
from services.order_service import models as order_models
from services.payment_service import models as payment_models
from services.session_service import models as session_models

from services.product_service.main import product_app
from services.order_service.main import order_app
from services.payment_service.main import payment_app
from services.session_service.main import session_app
from services.orchestrator.main import app as orchestrator_app

app = FastAPI(title="Ecommerce Cluster")

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        # Create schemas
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS product_schema"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS order_schema"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS payment_schema"))
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS session_schema"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

app.mount("/products", product_app)
app.mount("/orders", order_app)
app.mount("/payments", payment_app)
app.mount("/sessions", session_app)
app.mount("/orchestrator", orchestrator_app)