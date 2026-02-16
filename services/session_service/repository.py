from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
        # We use selectinload in the model, so items will be fetched automatically
        result = await db.execute(select(Session).where(Session.session_id == session_id))
        return result.scalars().first()

    @staticmethod
    async def add_item(db: AsyncSession, item: SessionItem):
        # Check if item exists in session to update quantity instead of duplicate
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