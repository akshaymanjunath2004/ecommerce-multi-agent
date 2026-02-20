from fastapi import APIRouter, HTTPException, Depends, Request
from shared.security import get_current_user, limiter
from .schemas import ChatRequest, ChatResponse
from .service import ChatService

router = APIRouter()
chat_service = ChatService() # Initialize Service

@router.get("/health")
async def health_check():
    return {"service": "orchestrator", "status": "running"}

# --- SECURE ENDPOINT ---
@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute per user/IP
async def chat_endpoint(
    request: Request,                          # REQUIRED: slowapi needs this to check IP/Headers
    payload: ChatRequest,                      # Your JSON body (renamed from 'request')
    user_id: str = Depends(get_current_user)   # REQUIRED: This locks the endpoint with JWT!
):
    try:
        # The endpoint is now secure! 
        # You now have the 'user_id' string available. In a future update, 
        # you can pass this to ChatService to enforce that users can only access their own sessions.
        
        response_text = await chat_service.process_message(
            session_id=payload.session_id,
            message=payload.message
        )
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))