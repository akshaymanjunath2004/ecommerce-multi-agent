from fastapi import FastAPI
from .router import router

payment_app = FastAPI(
    title="Payment Service",
    version="1.0.0"
)

payment_app.include_router(router)
