"""
Router now passes db: AsyncSession to service methods (async).
Previously called sync methods; now properly async end-to-end.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config.database import get_db
from shared.security.dependencies import get_current_user

from .schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from .service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
public_router = APIRouter()  # For any public endpoints (e.g. health check)

@public_router.get("/health", include_in_schema=False)
async def health_check():
    return {"service": "auth", "status": "running"}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    # FIX GAP #10: await async service method (was sync classmethod before)
    user = await AuthService.register(db, payload)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive a JWT access token",
)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    # FIX GAP #10: await async service method
    return await AuthService.login(db, payload)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user's profile",
)
async def get_me(
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await AuthService.get_user_by_id(db, int(user_id))