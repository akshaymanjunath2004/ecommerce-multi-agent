from fastapi import APIRouter, HTTPException, Depends, status
from shared.security import get_current_user
from .schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from .service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate):
    try:
        user = AuthService.register_user(payload.model_dump())
        return UserResponse(id=user["id"], email=user["email"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    try:
        token = AuthService.authenticate_user(payload.model_dump())
        return TokenResponse(access_token=token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.get("/me", response_model=dict)
async def get_me(user_id: str = Depends(get_current_user)):
    # get_current_user validates the JWT and extracts the 'sub'
    return {"user_id": user_id, "message": "You are authenticated"}