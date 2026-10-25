"""Automated tests for multi-turn agent conversation, caller verification, and isolation."""
import pytest
from app.agent.orchestrator import VoiceOpsAgent
from app.agent.memory import MemoryManager


@pytest.fixture
def agent():
    mem = MemoryManager()
    return VoiceOpsAgent(memory=mem)


def test_agent_first_turn_ai_greeting(agent):
    res = agent.respond("Hello, mujhe order ke baare mein help chahiye.", conversation_id="conv_1")
    assert res["decision"] == "clarify"
    reply = res["reply"]
    # Must identify as AI assistant
    assert any(k in reply.lower() for k in ["ai", "assistant", "एआई", "कृत्रिम"])


def test_agent_order_id_verification_gate(agent):
    agent.respond("Hello, help chahiye.", conversation_id="conv_2")
    res = agent.respond("Order number hai 8978 2837.", conversation_id="conv_2")
    assert res["decision"] == "clarify"
    assert any("lookup_order" in c for c in res["tool_calls"])
    reply = res["reply"].lower()
    # Must ask for phone last 4 digits OR pincode
    assert any(k in reply for k in ["last 4", "last four", "pincode", "pin code", "aakhri", "आख़िरी", "पिनकोड"])


def test_agent_verification_success(agent):
    agent.respond("Hello.", conversation_id="conv_3")
    agent.respond("Order number hai 8978 2837.", conversation_id="conv_3")
    res = agent.respond("Last four digits 4533 hain.", conversation_id="conv_3")
    assert res["decision"] == "answer"
    assert any("lookup_order(order_id=89782837, verification_value=4533)" in c for c in res["tool_calls"])
    assert any(k in res["reply"].lower() for k in ["verified", "सत्यापित", "help", "मदद"])


def test_agent_damage_escalation_handover(agent):
    agent.respond("Hello.", conversation_id="conv_4")
    agent.respond("Order number hai 8978 2837.", conversation_id="conv_4")
    agent.respond("Last four digits 4533 hain.", conversation_id="conv_4")
    res = agent.respond("Maine Zentro Vista 43-inch 4K Smart TV damage report kiya tha. Abhi replacement approve kar do na?", conversation_id="conv_4")
    assert res["decision"] == "escalate"
    assert any("create_ticket" in c for c in res["tool_calls"])
    # Must mention ticket / priority team, and must NOT falsely claim approval
    assert any(k in res["reply"].lower() for k in ["ticket", "priority", "टीम", "सहयोगी"])
    assert "has been approved" not in res["reply"].lower()


def test_agent_cross_customer_isolation(agent):
    # Customer A verifies order 89782837
    agent.respond("Hello.", conversation_id="conv_A")
    agent.respond("Order 8978 2837.", conversation_id="conv_A")
    agent.respond("4533", conversation_id="conv_A")
    
    # Customer B asks about refund without verifying
    res_b = agent.respond("What is my refund status?", conversation_id="conv_B")
    # Customer B must not receive Customer A's order details
    assert "89782837" not in res_b["reply"]
    assert "4533" not in res_b["reply"]
    assert res_b["decision"] == "clarify"


def test_agent_order_status_follow_up_after_verification(agent):
    """Regression test: Customer verifies order, then asks for order status in follow-up."""
    # Turn 1: Order inquiry
    res1 = agent.respond("Hello, I need help with my order 8978 2837.", conversation_id="conv_status_flow")
    assert res1["decision"] == "clarify"
    assert "89782837" in res1["reply"] or "8978 2837" in res1["reply"]
    assert "delivered" not in res1["reply"].lower()

    # Turn 2: Verification with registered phone suffix
    res2 = agent.respond("My phone ends with 4533.", conversation_id="conv_status_flow")
    assert res2["decision"] == "answer"
    assert any(k in res2["reply"].lower() for k in ["verified", "सत्यापित", "help", "kabir"])

    # Turn 3: Follow-up asking for current status WITHOUT repeating order ID
    res3 = agent.respond("What is the current status of my order?", conversation_id="conv_status_flow")
    assert res3["decision"] == "answer"
    # Must retrieve actual status from database ("delivered" for order 89782837)
    assert "delivered" in res3["reply"].lower()
    # Must NOT fallback to "Sorry, I don't have information about that"
    assert "don't have information" not in res3["reply"].lower()
    assert "89782837" in res3["reply"]
    assert any("TRK-1" in s for s in res3["source_chunks"])

    # Turn 4: Follow-up asking for items in the verified order
    res4 = agent.respond("What items did I buy in this order?", conversation_id="conv_status_flow")
    assert res4["decision"] == "answer"
    reply4 = res4["reply"].lower()
    assert any(k in reply4 for k in ["kestrel", "smartphone", "tv", "smart tv", "tote bag", "sootra"])

    # Turn 5: Follow-up asking for total price
    res5 = agent.respond("What was the total price paid?", conversation_id="conv_status_flow")
    assert res5["decision"] == "answer"
    assert "53127" in res5["reply"]


def test_agent_unauthorized_order_detail_rejection(agent):
    """Regression test: Unverified user cannot retrieve order status or details."""
    res = agent.respond("What is the current status of order 89782837?", conversation_id="conv_unauth_gate")
    # Must NOT reveal delivered status
    assert "delivered" not in res["reply"].lower()
    assert res["decision"] == "clarify"
    assert any(k in res["reply"].lower() for k in ["phone", "pincode", "last 4", "protect"])


def test_agent_cross_order_isolation_reverification(agent):
    """Regression test: Verification of order A does not permit access to order B."""
    # Customer verifies order 89782837
    agent.respond("Order 8978 2837", conversation_id="conv_cross_order")
    agent.respond("4533", conversation_id="conv_cross_order")

    # Customer asks about a DIFFERENT order 10023412
    res = agent.respond("What is the status of order 10023412?", conversation_id="conv_cross_order")
    # Must require re-verification for the new order
    assert res["decision"] == "clarify"
    assert "10023412" in res["reply"]
    assert any(k in res["reply"].lower() for k in ["phone", "pincode", "last 4", "protect"])


def test_agent_verification_and_status_in_single_turn(agent):
    """Regression test: Customer gives verification code and asks status in the same turn."""
    agent.respond("Order 8978 2837", conversation_id="conv_single_turn")
    res = agent.respond("4533, what is the current status of my order?", conversation_id="conv_single_turn")
    assert res["decision"] == "answer"
    assert "delivered" in res["reply"].lower()
    assert "89782837" in res["reply"]

