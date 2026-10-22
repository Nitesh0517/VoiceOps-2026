"""Tool request and response schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class OrderLookupResponse(BaseModel):
    found: bool = False
    verified: bool = False
    verification_required: bool = True
    order_id: Optional[str] = None
    message: Optional[str] = None
    status: Optional[str] = None
    total_inr: Optional[int] = None
    payment_method: Optional[str] = None
    delivered_on: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None
    customer_first_name: Optional[str] = None
    is_plus: Optional[bool] = None


class TicketCreateRequest(BaseModel):
    summary: str = Field(..., min_length=20, description="Escalation summary")
    order_id: Optional[str] = None
    reason: Optional[str] = None
    intent: Optional[str] = None


class TicketCreateResponse(BaseModel):
    created: bool
    ticket_id: Optional[str] = None
    error: Optional[str] = None
