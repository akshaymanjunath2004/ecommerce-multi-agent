import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Session, SessionItem
from .repository import SessionRepository
from .schemas import SessionCreate, SessionItemCreate

class SessionService:
    @staticmethod
    async def create_session(db: AsyncSession, data: SessionCreate):
        new_id = str(uuid.uuid4())
        session = Session(
            session_id=new_id,
            user_id=data.user_id,
            is_active=True
        )
        return await SessionRepository.create_session(db, session)

    @staticmethod
    async def get_session(db: AsyncSession, session_id: str):
        return await SessionRepository.get_session(db, session_id)

    @staticmethod
    async def add_item_to_session(db: AsyncSession, session_id: str, item_data: SessionItemCreate):
        item = SessionItem(
            session_id=session_id,
            product_id=item_data.product_id,
            quantity=item_data.quantity
        )
        await SessionRepository.add_item(db, item)
        return await SessionRepository.get_session(db, session_id)

    @staticmethod
    async def remove_item_from_session(db: AsyncSession, session_id: str, product_id: int):
        await SessionRepository.remove_item(db, session_id, product_id)
        return await SessionRepository.get_session(db, session_id)

    # --- NEW METHOD ---
    @staticmethod
    async def clear_session_cart(db: AsyncSession, session_id: str):
        await SessionRepository.clear_cart(db, session_id)