"""
FIX GAP #8: Added setup_observability() call.
Previously session_service produced no structured logs, traces, or metrics.
Every cart operation was invisible to the observability stack.
"""
from fastapi import FastAPI
from sqlalchemy import text

from shared.config.database import Base, engine
from shared.observability.setup import setup_observability

from .models import Session, SessionItem  
from .router import router, public_router

session_app = FastAPI(title="Session Service", version="2.0.0")

#Now emits structured logs, OTLP traces to Jaeger, and /metrics
setup_observability(session_app, "session_service")
session_app.include_router(public_router)
session_app.include_router(router)

@session_app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS session_schema"))
        await conn.run_sync(Base.metadata.create_all)