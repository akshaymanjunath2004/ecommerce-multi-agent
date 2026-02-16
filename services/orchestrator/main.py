from fastapi import FastAPI
from .router import router

# RENAME THIS from 'orchestrator_app' to 'app'
app = FastAPI(
    title="Orchestrator Service",
    version="1.0.0"
)

app.include_router(router)