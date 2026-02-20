"""
ALL endpoints now require the X-Internal-API-Key header.
Previously every endpoint was completely unprotected — any external caller
could create sessions, add items, or clear carts without authentication.

The APIRouter-level dependency means the protection applies to every route
defined here without repeating it per endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config.database import get_db
from shared.security.dependencies import verify_internal_api_key

from .schemas import SessionCreate, SessionItemCreate, SessionResponse
from .service import SessionService

router = APIRouter(dependencies=[Depends(verify_internal_api_key)])
public_router = APIRouter()  # For any public endpoints (e.g. health check)

@public_router.get("/health", include_in_schema=False)
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
async def add_item(
    session_id: str, item: SessionItemCreate, db: AsyncSession = Depends(get_db)
):
    session = await SessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await SessionService.add_item_to_session(db, session_id, item)


@router.delete("/{session_id}/items/{product_id}", response_model=SessionResponse)
async def remove_item(
    session_id: str, product_id: int, db: AsyncSession = Depends(get_db)
):
    session = await SessionService.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await SessionService.remove_item_from_session(db, session_id, product_id)


@router.delete("/{session_id}/items", status_code=204)
async def clear_cart(session_id: str, db: AsyncSession = Depends(get_db)):
    """Deletes all items in the session cart."""
    await SessionService.clear_session_cart(db, session_id)
    return