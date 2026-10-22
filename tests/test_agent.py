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
