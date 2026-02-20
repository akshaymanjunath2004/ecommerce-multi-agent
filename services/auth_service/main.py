"""
FIX GAP #3: Added schema creation on startup and setup_observability().
Previously the auth service started with no DB tables and produced
no structured logs, traces, or metrics.
"""
from fastapi import FastAPI
from sqlalchemy import text

from shared.config.database import Base, engine
from shared.observability.setup import setup_observability

from .models import User  # noqa: F401 — registers model with SQLAlchemy Base
from .router import router, public_router

auth_app = FastAPI(
    title="Auth Service",
    version="2.0.0",
    description="JWT authentication: register, login, token validation.",
)

# FIX GAP #3: Bootstrap observability (logging + tracing + metrics)
setup_observability(auth_app, "auth_service")

auth_app.include_router(router)
auth_app.include_router(public_router)

@auth_app.on_event("startup")
async def startup_event() -> None:
    # FIX GAP #3: Create auth_schema and users table on startup
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth_schema"))
        await conn.run_sync(Base.metadata.create_all)