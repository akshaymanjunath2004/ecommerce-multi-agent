from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health_check():
    return {"service": "payment", "status": "running"}
