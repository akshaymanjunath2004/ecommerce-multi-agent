from fastapi import FastAPI
from .router import router

app = FastAPI(title="Auth Service")

# Include the authentication routes
app.include_router(router)

@app.get("/")
async def root():
    return {"service": "auth", "status": "running"}