from fastapi import FastAPI
from .router import router

session_app = FastAPI(
    title="Session Service",
    version="1.0.0"
)

session_app.include_router(router)
