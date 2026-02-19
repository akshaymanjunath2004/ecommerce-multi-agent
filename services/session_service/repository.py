from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from .models import Session, SessionItem

class SessionRepository:
    @staticmethod
    async def create_session(db: AsyncSession, session: Session):
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session(db: AsyncSession, session_id: str):
        result = await db.execute(select(Session).where(Session.session_id == session_id))
        return result.scalars().first()

    @staticmethod
    async def add_item(db: AsyncSession, item: SessionItem):
        result = await db.execute(
            select(SessionItem)
            .where(SessionItem.session_id == item.session_id)
            .where(SessionItem.product_id == item.product_id)
        )
        existing_item = result.scalars().first()

        if existing_item:
            existing_item.quantity += item.quantity
        else:
            db.add(item)
            
        await db.commit()
        return True
    
    @staticmethod
    async def remove_item(db: AsyncSession, session_id: str, product_id: int):
        stmt = delete(SessionItem).where(
            SessionItem.session_id == session_id,
            SessionItem.product_id == product_id
        )
        await db.execute(stmt)
        await db.commit()

    # --- CRITICAL FIX ---
    @staticmethod
    async def clear_cart(db: AsyncSession, session_id: str):
        """Deletes all items for the session and forces a commit."""
        stmt = delete(SessionItem).where(SessionItem.session_id == session_id)
        await db.execute(stmt)
        await db.commit() # Ensure this commit is awaited!