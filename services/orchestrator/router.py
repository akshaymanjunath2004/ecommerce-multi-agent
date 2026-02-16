from fastapi import APIRouter, HTTPException
from .schemas import ChatRequest, ChatResponse
from .service import ChatService

router = APIRouter()
chat_service = ChatService() # Initialize Service

@router.get("/health")
async def health_check():
    return {"service": "orchestrator", "status": "running"}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response_text = await chat_service.process_message(
            session_id=request.session_id,
            message=request.message
        )
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))