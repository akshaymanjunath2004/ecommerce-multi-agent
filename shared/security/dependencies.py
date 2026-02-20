from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from .jwt_handler import verify_access_token
from .api_key import verify_api_key

# Defines the expected header format (Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# Defines the expected internal service header
api_key_header = APIKeyHeader(name="X-Internal-API-Key", auto_error=False)

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)) -> str:
    """Dependency to validate JWT and return the user ID (sub)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
        
    payload = verify_access_token(token)
    if payload is None:
        raise credentials_exception
        
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
        
    # Store in request state for downstream use (like rate limiting)
    request.state.user_id = user_id
    return user_id

async def verify_internal_api_key(api_key: str = Depends(api_key_header)) -> bool:
    """Dependency to validate service-to-service internal requests."""
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-Internal-API-Key header"
        )
    return True