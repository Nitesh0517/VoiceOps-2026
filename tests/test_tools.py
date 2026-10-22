"""Automated tests for order lookup and ticket creation tools."""
import pytest
from app.tools.order_tool import OrderTool
from app.tools.ticket_tool import TicketTool


@pytest.fixture(scope="module")
def tools():
    return OrderTool(), TicketTool()


def test_lookup_order_unverified_protection(tools):
    order_tool, _ = tools
    res = order_tool.lookup_order("89782837")
    assert res.get("verification_required") is True
    assert "items" not in res
    assert "status" not in res
    assert "phone" not in res


def test_lookup_order_invalid_verification(tools):
    order_tool, _ = tools
    res = order_tool.lookup_order("89782837", verification_value="0000")
    assert res.get("verified") is False
    assert "items" not in res


def test_lookup_order_verified_phone_suffix(tools):
    order_tool, _ = tools
    # C100181 phone suffix is 4533
    res = order_tool.lookup_order("89782837", verification_value="4533")
    assert res.get("verified") is True
    assert res.get("found") is True
    assert "items" in res
    assert "status" in res
    assert "phone_last4" not in res  # Never reveal secret


def test_lookup_order_verified_pincode(tools):
    order_tool, _ = tools
    # Order 89782837 delivery pincode is 781006
    res = order_tool.lookup_order("89782837", verification_value="781006")
    assert res.get("verified") is True
    assert res.get("found") is True


def test_create_ticket_validation(tools):
    _, ticket_tool = tools
    fail = ticket_tool.create_ticket("short")
    assert fail.get("created") is False
    
    succ = ticket_tool.create_ticket(
        summary="Customer reports broken screen on 43-inch TV. Requesting priority replacement.",
        order_id="89782837",
        reason="high_value_damage",
        intent="damage"
    )
    assert succ.get("created") is True
    assert succ.get("ticket_id").startswith("TKT")
