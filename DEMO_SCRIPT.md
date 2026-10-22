# VoiceOps 2026 — 2-Minute Demo Script

This script provides the complete walkthrough for the 2-minute submission video demo, showcasing all required competencies:
1. **Introduction & Self-Identification as AI Assistant**
2. **Grounded Policy Question Answered with Citations**
3. **Multi-Turn Follow-Up (Coreference & Calendar Math)**
4. **Caller Identity Verification Gate (`lookup_order`)**
5. **Human Escalation / Handover Ticket (`create_ticket`)**
6. **Graceful Refusal on Unsupported Question ("I don't have information...")**
7. **End-to-End Voice Interaction (Gnani STT & TTS)**

---

## Demo Walkthrough (2 Minutes)

### Scene 1: Introduction & First Turn Greeting (0:00 - 0:20)
* **Customer Audio / Input**: "Hello, mujhe apne order ke baare mein help chahiye."
* **System Action**:
  - Gnani STT transcribes the speech.
  - Agent detects Turn 1, introduces itself as an AI assistant, and prompts for the Order ID.
* **Agent Voice Output**:
  > *"नमस्ते! मैं ZentroMart का AI कस्टमर सपोर्ट असिस्टेंट हूँ। कृपया मुझे अपना 8 अंकों का ऑर्डर नंबर (Order ID) बताएं, ताकि मैं आपकी सहायता कर सकूँ।"*

---

### Scene 2: Caller Identity Verification Gate (0:20 - 0:45)
* **Customer Audio / Input**: "Mera order number hai 8978 2837."
* **System Action**:
  - Agent triggers `lookup_order(89782837)`.
  - Identity verification gate activates: no private order details are revealed.
  - Agent challenges the caller for registered phone last 4 digits or delivery pincode.
* **Agent Voice Output**:
  > *"ऑर्डर विवरण की सुरक्षा के लिए, कृपया अपने रजिस्टर्ड फ़ोन नंबर के आख़िरी 4 अंक (last 4 digits) या डिलीवरी पिनकोड बताएं।"*
* **Customer Audio / Input**: "Aakhri 4 ank 4533 hain."
* **System Action**:
  - Agent calls `lookup_order(89782837, verification_value=4533)`.
  - Verification succeeds! Session unlocks customer first name and order items (Zentro Vista 43-inch Smart TV).
* **Agent Voice Output**:
  > *"धन्यवाद, आपकी पहचान सत्यापित हो गई है। मैं आपके ऑर्डर 8 9 7 8, 2 8 3 7 में कैसे मदद कर सकता हूँ?"*

---

### Scene 3: High-Value Damage Escalation & Handover (0:45 - 1:15)
* **Customer Audio / Input**: "Maine Zentro Vista 43-inch Smart TV damage report kiya tha. Abhi replacement approve kar do na?"
* **System Action**:
  - Agent checks item value (₹21,999 > ₹10,000 threshold under policy `DWM-3`).
  - AI does not approve claim directly.
  - Calls `create_ticket(summary=..., reason='high_value_damage')`.
  - Returns ticket confirmation with ticket ID.
* **Agent Voice Output**:
  > *"ZentroMart की डैमेज पॉलिसी के अनुसार, ₹10,000 से अधिक के क्लेम का रिव्यू हमारी Priority Resolution टीम करती है। मैंने आपकी समस्या के लिए टिकट TKT89782837 बना दी है। हमारी टीम जल्द ही आपसे संपर्क करेगी।"*

---

### Scene 4: Grounded Policy Question & Coreference Follow-Up (1:15 - 1:40)
* **Customer Audio / Input**: "Wallet refund mein kitna time lagta hai?"
* **System Action**:
  - RAG retrieves `REF-2` / `KB-00.1` (Wallet policy overrides FAQ).
* **Agent Voice Output**:
  > *"ZentroMart Wallet में रिफ़ंड तुरंत (instant, 2 घंटे के भीतर) प्रोसेस हो जाता है।"*
* **Customer Audio / Input**: "Aur agar credit card pe hota toh?" (Multi-turn coreference)
* **System Action**:
  - Resolves coreference: same refund topic, applies 5-7 business days rule, skipping Sundays and holidays.
* **Agent Voice Output**:
  > *"क्रेडिट कार्ड रिफ़ंड में 5 से 7 कार्यदिवस (business days) लगते हैं, जिसमें रविवार और वेयरहाउस की छुट्टियां नहीं गिनी जाती हैं।"*

---

### Scene 5: Unsupported Question Refusal (1:40 - 2:00)
* **Customer Audio / Input**: "Can I schedule a delivery at midnight?"
* **System Action**:
  - RAG detects zero document coverage (`is_answerable = False`).
  - Refuses gracefully without hallucinating false policies.
* **Agent Voice Output**:
  > *"Sorry, I don't have information about that. I can connect you to a colleague who can help."*
* **Closing**: End demo showing generated WAV files in UI / terminal.
