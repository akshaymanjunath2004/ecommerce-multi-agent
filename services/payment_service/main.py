"""
FIX GAP #7: Added setup_observability() call.
Previously payment_service produced no structured logs, traces, or metrics —
it was a blind spot in the entire observability stack.
"""
from fastapi import FastAPI
from sqlalchemy import text

from shared.config.database import Base, engine
from shared.observability.setup import setup_observability 

from .models import Payment 
from .router import router, public_router


payment_app = FastAPI(title="Payment Service", version="2.0.0")

# Now emits structured logs, OTLP traces to Jaeger, and /metrics
setup_observability(payment_app, "payment_service")

payment_app.include_router(router)
payment_app.include_router(public_router)

@payment_app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS payment_schema"))
        await conn.run_sync(Base.metadata.create_all)