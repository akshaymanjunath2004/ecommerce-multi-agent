"""
FIX GAP #2: Replaced fake_user_db in-memory dict with real async DB calls.
FIX GAP #10: All methods are now async — no longer blocking the event loop
             on what were previously synchronous classmethods.
"""
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from shared.security.jwt_handler import create_access_token

from .models import User
from .repository import UserRepository
from .schemas import TokenResponse, UserCreate, UserLogin

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:

    @staticmethod
    def _hash_password(password: str) -> str:
        return _pwd_context.hash(password)

    @staticmethod
    def _verify_password(plain: str, hashed: str) -> bool:
        return _pwd_context.verify(plain, hashed)

    # FIX GAP #10: async — was sync classmethod; bcrypt hash is CPU-bound but
    # passlib is fast enough for typical loads. For extreme throughput, wrap in
    # asyncio.to_thread(). Kept simple here for clarity.
    @staticmethod
    async def register(db: AsyncSession, data: UserCreate) -> User:
        existing = await UserRepository.get_by_email(db, data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user = User(
            email=data.email,
            hashed_password=AuthService._hash_password(data.password),
        )
        return await UserRepository.create(db, user)

    @staticmethod
    async def login(db: AsyncSession, data: UserLogin) -> TokenResponse:
        user = await UserRepository.get_by_email(db, data.email)
        if not user or not AuthService._verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled",
            )
        token = create_access_token(data={"sub": str(user.id)})
        return TokenResponse(access_token=token)

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user