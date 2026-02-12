from fastapi import FastAPI
from .router import router

order_app = FastAPI(
    title="Order Service",
    version="1.0.0"
)

order_app.include_router(router)
