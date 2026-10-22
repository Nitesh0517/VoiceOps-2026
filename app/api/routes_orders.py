"""Orders and Tickets router."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.tools.order_tool import OrderTool
from app.tools.ticket_tool import TicketTool
from app.schemas.tools import OrderLookupResponse, TicketCreateRequest, TicketCreateResponse

router = APIRouter(tags=["Orders & Tickets"])
order_tool = OrderTool()
ticket_tool = TicketTool()


@router.get("/orders/{order_id}", response_model=OrderLookupResponse)
def get_order_details(
    order_id: str,
    verification_value: Optional[str] = Query(None, description="Phone last 4 digits or delivery pincode")
):
    """Identity-gated order lookup."""
    res = order_tool.lookup_order(order_id, verification_value=verification_value)
    return OrderLookupResponse(**res)


@router.post("/tickets", response_model=TicketCreateResponse)
def create_support_ticket(req: TicketCreateRequest):
    """Log an escalation ticket."""
    res = ticket_tool.create_ticket(
        summary=req.summary,
        order_id=req.order_id,
        reason=req.reason,
        intent=req.intent
    )
    if not res.get("created"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to create ticket"))
    return TicketCreateResponse(created=True, ticket_id=res.get("ticket_id"))
