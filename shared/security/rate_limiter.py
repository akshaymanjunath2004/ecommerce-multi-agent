from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from .jwt_handler import verify_access_token

def user_id_or_ip(request: Request) -> str:
    """
    Key function for SlowAPI. 
    Extracts the user ID directly from the Authorization header if available.
    Falls back to the client's IP address if unauthenticated.
    """
    auth_header = request.headers.get("Authorization")
    
    # Try to extract User ID from JWT
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = verify_access_token(token)
        if payload and "sub" in payload:
            return f"user:{payload['sub']}"
            
    # Fallback to IP address (handles proxies if X-Forwarded-For is set correctly by Uvicorn)
    return f"ip:{get_remote_address(request)}"

# Initialize the Limiter with our custom key function
limiter = Limiter(key_func=user_id_or_ip)