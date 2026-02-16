from pydantic import BaseModel

class OrderCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float # In a real app, we'd fetch this from Product Service, but passed here for simplicity

class OrderResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    total_price: float
    status: str

    class Config:
        from_attributes = True