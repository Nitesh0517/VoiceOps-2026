"""Tools package."""
from app.tools.order_tool import OrderTool
from app.tools.ticket_tool import TicketTool

_order_tool = OrderTool()
_ticket_tool = TicketTool()


def lookup_order(order_id: str, verification_value: str = None):
    return _order_tool.lookup_order(order_id, verification_value)


def create_ticket(summary: str, order_id: str = None, reason: str = None, intent: str = None):
    return _ticket_tool.create_ticket(summary, order_id, reason, intent)


__all__ = ["OrderTool", "TicketTool", "lookup_order", "create_ticket"]
