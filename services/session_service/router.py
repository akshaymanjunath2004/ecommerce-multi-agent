from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from shared.config.database import get_db
from .schemas import SessionCreate, SessionResponse, SessionItemCreate
from .service import SessionService

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"service": "session", "status": "running"}

@router.post("/", response_model=SessionResponse)
async def create_session(data: SessionCreate, db: AsyncSession = Depends(get_db)):
    return await SessionService.create_session(db, data)

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await SessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/{session_id}/items", response_model=SessionResponse)
async def add_item(session_id: str, item: SessionItemCreate, db: AsyncSession = Depends(get_db)):
    # Verify session exists first
    session = await SessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return await SessionService.add_item_to_session(db, session_id, item)