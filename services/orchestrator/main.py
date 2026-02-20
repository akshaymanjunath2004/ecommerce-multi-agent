from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from shared.security import limiter
from shared.observability import setup_observability
from .router import router

app = FastAPI(
    title="Orchestrator Service",
    version="1.0.0"
)

# --- OBSERVABILITY BOOTSTRAP ---
setup_observability(app, "orchestrator_service")

# --- SECURITY SETUP ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(router)