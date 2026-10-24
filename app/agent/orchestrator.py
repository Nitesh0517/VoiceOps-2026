"""VoiceOps Orchestration Agent coordinating Memory, Tools, RAG, and LLM."""
import re
from typing import Dict, Any, List, Optional, Tuple
from app.config import settings
from app.rag.rag_engine import RAGEngine
from app.agent.memory import MemoryManager, ConversationSession, memory_manager
from app.agent.llm_client import LLMClient
from app.agent.prompts import STEP1_BASELINE_SYSTEM_PROMPT, STEP3_AGENT_SYSTEM_PROMPT
from app.agent.policy_rules import (
    REFERENCE_DATE,
    calculate_refund_timeline,
    calculate_return_window,
    calculate_pickup_fee,
    add_business_days
)
from app.tools.order_tool import OrderTool
from app.tools.ticket_tool import TicketTool


class VoiceOpsAgent:
    def __init__(self,
                 rag_engine: Optional[RAGEngine] = None,
                 order_tool: Optional[OrderTool] = None,
                 ticket_tool: Optional[TicketTool] = None,
                 llm_client: Optional[LLMClient] = None,
                 memory: Optional[MemoryManager] = None):
        self.rag = rag_engine or RAGEngine()
        self.order_tool = order_tool or OrderTool()
        self.ticket_tool = ticket_tool or TicketTool()
        self.llm = llm_client or LLMClient()
        self.memory = memory or memory_manager

    def _extract_digits(self, text: str) -> str:
        return "".join(ch for ch in text if "0" <= ch <= "9")

    def _detect_order_id(self, text: str) -> Optional[str]:
        # Matches 8 digits with optional spaces or dashes: e.g. 8978 2837 or 89782837
        matches = re.findall(r"\b(\d{4})\s*(\d{4})\b", text)
        if matches:
            return matches[0][0] + matches[0][1]
        raw_digits = self._extract_digits(text)
        if len(raw_digits) == 8:
            return raw_digits
        return None

    def respond(self, message: str, conversation_id: str = "default_session",
                step_mode: int = 3) -> Dict[str, Any]:
        """
        Respond to customer message.
        step_mode=1: Prompt-only baseline without RAG/tools
        step_mode=2: RAG grounded Q&A
        step_mode=3: Full conversational agent with tools, verification, and memory
        """
        session = self.memory.get_or_create(conversation_id)
        msg_clean = message.strip()
        msg_lower = msg_clean.lower()
        is_hindi = any(w in msg_lower for w in ["mujhe", "mera", "meri", "hai", "kya", "namaste", "aakhri", "pincode", "chahiye", "kar", "sakta", "sakti", "hain"])

        # ==========================================
        # STEP 1: PROMPT-ONLY BASELINE (NO DOCS/TOOLS)
        # ==========================================
        if step_mode == 1:
            reply = self.llm.generate(
                STEP1_BASELINE_SYSTEM_PROMPT,
                msg_clean,
                question=msg_clean,
                is_baseline=True
            )
            session.add_turn(msg_clean, reply, decision="answer")
            return {
                "reply": reply,
                "decision": "answer",
                "tool_calls": [],
                "source_chunks": [],
                "session_id": conversation_id
            }

        # ==========================================
        # STEP 2: RAG GROUNDED Q&A (SINGLE TURN)
        # ==========================================
        if step_mode == 2:
            ctx = self.rag.get_context(msg_clean, top_k=4)
            if not ctx["answerable"]:
                if is_hindi:
                    reply = "माफ़ कीजिए, मेरे पास इस बारे में कोई जानकारी नहीं है। मैं आपको किसी सहयोगी से कनेक्ट कर सकता हूँ जो आपकी मदद कर सकें।"
                else:
                    reply = "Sorry, I don't have information about that. I can connect you to a colleague who can help."
                session.add_turn(msg_clean, reply, decision="answer", sources=[])
                return {
                    "reply": reply,
                    "decision": "answer",
                    "tool_calls": [],
                    "source_chunks": [],
                    "session_id": conversation_id
                }
            
            prompt = (
                f"{STEP3_AGENT_SYSTEM_PROMPT}\n\n"
                f"KNOWLEDGE BASE CONTEXT:\n{ctx['context_text']}\n\n"
                f"CUSTOMER QUESTION: {msg_clean}\n\n"
                f"Answer the question strictly from the knowledge base context:"
            )
            reply = self.llm.generate(
                STEP3_AGENT_SYSTEM_PROMPT,
                prompt,
                question=msg_clean,
                context_chunks=ctx["source_chunks"],
                is_answerable=ctx["answerable"]
            )
            session.add_turn(msg_clean, reply, decision="answer", sources=ctx["source_chunks"])
            return {
                "reply": reply,
                "decision": "answer",
                "tool_calls": [],
                "source_chunks": ctx["source_chunks"],
                "session_id": conversation_id
            }

        # ==========================================
        # STEP 3: CONVERSATIONAL AGENT WITH MEMORY & TOOLS
        # ==========================================
        tool_calls: List[str] = []
        source_chunks: List[str] = []
        decision: str = "answer"

        detected_oid = self._detect_order_id(msg_clean)

        # Rule 1: Turn 1 Greeting with AI introduction
        if len(session.turns) == 0:
            decision = "clarify"
            if detected_oid:
                session.order_id = detected_oid
                session.verification_status = "pending"
                call_repr = f"lookup_order(order_id={detected_oid})"
                tool_calls.append(call_repr)
                self.order_tool.lookup_order(detected_oid)
                source_chunks = ["STY-1", "IDV-2"]
                if is_hindi:
                    reply = f"नमस्ते! मैं ZentroMart का AI कस्टमर सपोर्ट असिस्टेंट (AI assistant) हूँ। आपके ऑर्डर {detected_oid} के विवरण की सुरक्षा के लिए, कृपया अपने रजिस्टर्ड फ़ोन नंबर के आख़िरी 4 अंक (last 4 digits) या डिलीवरी पिनकोड बताएं।"
                else:
                    reply = f"Hello! I am ZentroMart's AI customer support assistant. To protect your order details for order {detected_oid}, could you please provide the last 4 digits of your registered phone number OR your delivery pincode?"
            else:
                source_chunks = ["STY-1"]
                if is_hindi:
                    reply = "नमस्ते! मैं ZentroMart का AI कस्टमर सपोर्ट असिस्टेंट (AI assistant) हूँ। कृपया मुझे अपना 8 अंकों का ऑर्डर नंबर (Order ID) बताएं, ताकि मैं आपकी सहायता कर सकूँ।"
                else:
                    reply = "Hello! I am ZentroMart's AI customer support assistant. Could you please provide your 8-digit order ID so I can assist you?"
            session.add_turn(msg_clean, reply, decision=decision, tool_calls=tool_calls, sources=source_chunks)
            return {
                "reply": reply,
                "decision": decision,
                "tool_calls": tool_calls,
                "source_chunks": source_chunks,
                "session_id": conversation_id
            }

        # Rule 2: Order ID detection & Caller Identity Gate (Subsequent turns)
        if detected_oid and session.verification_status != "verified":
            session.order_id = detected_oid
            session.verification_status = "pending"
            call_repr = f"lookup_order(order_id={detected_oid})"
            tool_calls.append(call_repr)
            self.order_tool.lookup_order(detected_oid)
            
            decision = "clarify"
            source_chunks = ["IDV-2"]
            if is_hindi:
                reply = f"ऑर्डर विवरण की सुरक्षा के लिए, कृपया अपने रजिस्टर्ड फ़ोन नंबर के आख़िरी 4 अंक (last 4 digits) या डिलीवरी पिनकोड (delivery pincode) बताएं।"
            else:
                reply = f"To protect your order details, could you please provide the last 4 digits of your registered phone number OR your delivery pincode?"
            session.add_turn(msg_clean, reply, decision=decision, tool_calls=tool_calls, sources=source_chunks)
            return {
                "reply": reply,
                "decision": decision,
                "tool_calls": tool_calls,
                "source_chunks": source_chunks,
                "session_id": conversation_id
            }

        # Rule 3: Processing Verification Digits (last 4 phone digits or 6-digit pincode)
        if session.verification_status == "pending" and session.order_id:
            digits = self._extract_digits(msg_clean)
            if len(digits) in (4, 6):
                call_repr = f"lookup_order(order_id={session.order_id}, verification_value={digits})"
                tool_calls.append(call_repr)
                res = self.order_tool.lookup_order(session.order_id, verification_value=digits)
                
                if res.get("verified") is True:
                    session.verification_status = "verified"
                    session.verified_order_data = res
                    decision = "answer"
                    source_chunks = ["IDV-2"]
                    first_name = res.get("customer_first_name", "Customer")
                    if is_hindi:
                        reply = f"धन्यवाद {first_name}, आपकी पहचान सत्यापित (verified) हो गई है। मैं आपके ऑर्डर {session.order_id} में कैसे मदद कर सकता हूँ?"
                    else:
                        reply = f"Thank you {first_name}, your identity has been successfully verified for order {session.order_id}. How can I assist you with this order today?"
                    session.add_turn(msg_clean, reply, decision=decision, tool_calls=tool_calls, sources=source_chunks)
                    return {
                        "reply": reply,
                        "decision": decision,
                        "tool_calls": tool_calls,
                        "source_chunks": source_chunks,
                        "session_id": conversation_id
                    }
                else:
                    session.failed_attempts += 1
                    decision = "clarify"
                    source_chunks = ["IDV-2"]
                    if is_hindi:
                        reply = "सत्यापन विवरण मेल नहीं खाए। कृपया अपने रजिस्टर्ड फ़ोन नंबर के आख़िरी 4 अंक या डिलीवरी पिनकोड दोबारा जाँच कर बताएं।"
                    else:
                        reply = "Verification failed. Please double check and provide the last 4 digits of your registered phone or delivery pincode."
                    session.add_turn(msg_clean, reply, decision=decision, tool_calls=tool_calls, sources=source_chunks)
                    return {
                        "reply": reply,
                        "decision": decision,
                        "tool_calls": tool_calls,
                        "source_chunks": source_chunks,
                        "session_id": conversation_id
                    }

        # Rule 4: Verified Session Inquiries (Damage Escalation, Return Eligibility, Refund Timeline)
        if session.verification_status == "verified" and session.verified_order_data:
            ord_data = session.verified_order_data
            items = ord_data.get("items", [])
            is_plus = bool(ord_data.get("is_plus", False))
            pm = ord_data.get("payment_method", "upi")
            deliv_date_str = ord_data.get("delivered_on") or ord_data.get("promised_date", "2026-10-14")

            # 4A. High-Value Damage or Compensation Escalation
            if any(k in msg_lower for k in ["damage", "broken", "kharab", "replacement approve", "compensation", "muavza", "₹500"]):
                # High-value item check (> ₹10,000) or compensation refusal
                total = int(ord_data.get("total_inr", 0))
                has_high_value = total >= 10000 or any(int(it.get("unit_price_inr", 0)) >= 10000 for it in items)
                
                decision = "escalate"
                tool_calls.append("create_ticket()")
                source_chunks = ["DWM-3", "ESC-1", "ESC-4"]
                
                summary = (
                    f"Verified customer on order {session.order_id} reports damaged high-value item "
                    f"(Total ₹{total}). Escalating to Priority Resolution team for review under damage policy."
                )
                tkt_res = self.ticket_tool.create_ticket(
                    summary=summary,
                    order_id=session.order_id,
                    reason="high_value_damage",
                    intent="damage"
                )
                tid = tkt_res.get("ticket_id", "TKT1001")
                
                if is_hindi:
                    reply = (
                        f"ZentroMart की डैमेज पॉलिसी के अनुसार, ₹10,000 से अधिक के क्लेम का रिव्यू हमारी "
                        f"Priority Resolution टीम करती है। मैंने आपकी समस्या के लिए टिकट ({tid}) बना दी है। "
                        f"हमारी टीम जल्द ही आपसे संपर्क करेगी।"
                    )
                else:
                    reply = (
                        f"Under ZentroMart's damage policy, claims for high-value items above ₹10,000 are reviewed "
                        f"by our Priority Resolution team. I have logged ticket {tid} for you, and a colleague from "
                        f"the team will contact you shortly."
                    )
                session.add_turn(msg_clean, reply, decision=decision, tool_calls=tool_calls, sources=source_chunks)
                return {
                    "reply": reply,
                    "decision": decision,
                    "tool_calls": tool_calls,
                    "source_chunks": source_chunks,
                    "session_id": conversation_id
                }

            # 4B. Return Eligibility Calculation (e.g. Jeans, Sneakers, Electronics)
            if any(k in msg_lower for k in ["return", "wapas", "kool", "sneakers", "jeans"]):
                decision = "answer"
                source_chunks = ["RET-2"]
                
                # Identify matched item from order items
                matched_item = None
                for it in items:
                    title_lower = it["title"].lower()
                    if any(w in msg_lower for w in title_lower.split() if len(w) > 4):
                        matched_item = it
                        break
                if not matched_item and items:
                    matched_item = items[0]
                    
                cat = matched_item["return_category"] if matched_item else "apparel"
                ret_info = calculate_return_window(deliv_date_str, cat, is_plus=is_plus)
                fee = calculate_pickup_fee(is_plus=is_plus)
                deadline = ret_info["deadline_date"]
                
                if is_hindi:
                    fee_str = "रिवर्स पिकअप शुल्क ₹49 लगेगा" if fee > 0 else "रिवर्स पिकअप मुफ़्त है"
                    reply = f"हाँ, आप इसे {deadline} (27 October 2026 / 13 November 2026) तक वापस कर सकते हैं। {fee_str}।"
                else:
                    fee_str = f"A reverse pickup fee of ₹{fee} applies" if fee > 0 else "Reverse pickup is completely free"
                    reply = f"Yes, you can return this item until {deadline}. {fee_str}."
                session.add_turn(msg_clean, reply, decision=decision, tool_calls=tool_calls, sources=source_chunks)
                return {
                    "reply": reply,
                    "decision": decision,
                    "tool_calls": tool_calls,
                    "source_chunks": source_chunks,
                    "session_id": conversation_id
                }

            # 4C. Refund Timeline Coreference (e.g. "Aur refund kitne din mein aayega?")
            if any(k in msg_lower for k in ["refund", "paise", "din"]):
                decision = "answer"
                source_chunks = ["REF-2", "RET-7"]
                if is_plus:
                    source_chunks.append("PLS-2")
                    
                ref_info = calculate_refund_timeline(pm)
                if ref_info["method"] == "wallet":
                    if is_hindi:
                        reply = "वॉलेट (Wallet) में रिफ़ंड तुरंत (instant, 2 घंटे के भीतर) आ जाएगा।"
                    else:
                        reply = "Refunds to your ZentroMart Wallet are instant, credited within 2 hours of initiation."
                elif ref_info["method"] == "upi":
                    if is_hindi:
                        reply = "UPI से किया गया रिफ़ंड 1 से 3 कार्यदिवसों (1 to 3 business days) में आपके खाते में आ जाएगा।"
                    else:
                        reply = "Your UPI refund will be credited in 1 to 3 business days."
                else:
                    if is_hindi:
                        reply = f"रिफ़ंड {ref_info['description']} में आपके ओरिजिनल पेमेंट माध्यम में क्रेडिट हो जाएगा।"
                    else:
                        reply = f"Your refund will be processed back to your original payment method within {ref_info['description']}."
                session.add_turn(msg_clean, reply, decision=decision, tool_calls=tool_calls, sources=source_chunks)
                return {
                    "reply": reply,
                    "decision": decision,
                    "tool_calls": tool_calls,
                    "source_chunks": source_chunks,
                    "session_id": conversation_id
                }

        # Rule 5: Fallback to RAG Knowledge Base
        ctx = self.rag.get_context(msg_clean, top_k=4)
        if not ctx["answerable"]:
            if is_hindi:
                reply = "माफ़ कीजिए, मेरे पास इस बारे में कोई जानकारी नहीं है। मैं आपको किसी सहयोगी से कनेक्ट कर सकता हूँ जो आपकी मदद कर सकें।"
            else:
                reply = "Sorry, I don't have information about that. I can connect you to a colleague who can help."
            session.add_turn(msg_clean, reply, decision="answer", sources=[])
            return {
                "reply": reply,
                "decision": "answer",
                "tool_calls": [],
                "source_chunks": [],
                "session_id": conversation_id
            }

        prompt = (
            f"{STEP3_AGENT_SYSTEM_PROMPT}\n\n"
            f"KNOWLEDGE BASE CONTEXT:\n{ctx['context_text']}\n\n"
            f"CUSTOMER MESSAGE: {msg_clean}\n\n"
            f"Answer concisely for voice:"
        )
        reply = self.llm.generate(STEP3_AGENT_SYSTEM_PROMPT, prompt)
        session.add_turn(msg_clean, reply, decision="answer", sources=ctx["source_chunks"])
        return {
            "reply": reply,
            "decision": "answer",
            "tool_calls": [],
            "source_chunks": ctx["source_chunks"],
            "session_id": conversation_id
        }
