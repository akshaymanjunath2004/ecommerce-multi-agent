from fastapi import FastAPI
from sqlalchemy import text

from shared.config.database import Base, engine
from shared.observability.setup import setup_observability

from .models import User # Import to register with Base
from .router import router, public_router

auth_app = FastAPI(
    title="Auth Service",
    version="2.0.0",
    description="JWT authentication: register, login, token validation.",
)

#Bootstrap observability (logging + tracing + metrics)
setup_observability(auth_app, "auth_service")

auth_app.include_router(router)
auth_app.include_router(public_router)

@auth_app.on_event("startup")
async def startup_event() -> None:
    #Create auth_schema and users table on startup
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth_schema"))
        await conn.run_sync(Base.metadata.create_all)