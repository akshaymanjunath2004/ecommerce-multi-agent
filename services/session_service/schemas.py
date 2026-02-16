from pydantic import BaseModel
from typing import List, Optional

class SessionItemCreate(BaseModel):
    product_id: int
    quantity: int

class SessionItemResponse(BaseModel):
    product_id: int
    quantity: int

    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    user_id: Optional[int] = None

class SessionResponse(BaseModel):
    session_id: str
    user_id: Optional[int]
    is_active: bool
    items: List[SessionItemResponse] = []

    class Config:
        from_attributes = True