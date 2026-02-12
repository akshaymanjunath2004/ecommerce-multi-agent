from fastapi import FastAPI
from .router import router

orchestrator_app = FastAPI(
    title="Orchestrator Service",
    version="1.0.0"
)

orchestrator_app.include_router(router)
