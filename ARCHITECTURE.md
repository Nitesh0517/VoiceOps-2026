# VoiceOps 2026 — Architecture & System Design

## 1. Architectural Overview

```mermaid
flowchart TD
    User([Customer: Voice or Text]) --> UI[Streamlit UI / Batch run.py / REST API]
    
    subgraph Voice_Layer["Voice Layer (Gnani.ai)"]
        UI -->|Audio WAV| STT["Gnani STT REST (en-IN, hi-IN)"]
        STT -->|Transcript| Agent
        Agent -->|Reply Text| Norm["Speech Normalizer (normalizer.py)"]
        Norm --> TTS["Gnani TTS REST (timbre-v2.5 Kaveri)"]
        TTS -->|Speech Audio| OutAudio([Spoken Audio Output])
    end

    subgraph Agent_Core["Orchestration Agent (app/agent/)"]
        Agent[VoiceOps Orchestrator]
        Mem[(Session Memory & Coreference)] <--> Agent
        Rules[Deterministic Policy Rules] <--> Agent
        LLM[Multi-Backend LLM: Gemini / OpenAI / Offline] <--> Agent
    end

    subgraph Grounding_Layer["RAG & Data Layer"]
        Agent -->|Query| RAG[Hybrid RAG Engine]
        RAG --> Docs[(21 KB Policy Documents)]
        RAG --> Precedence[Precedence Reranker]
        
        Agent -->|Tool Call| Tools[Tools Registry]
        Tools --> OrderTool[Identity-Gated Order Tool]
        Tools --> TicketTool[Escalation Ticket Tool]
        
        OrderTool <--> DB[(SQLite: zentromart.db)]
        TicketTool --> DB
        TicketTool --> CSVLogs[(tickets_created.csv)]
    end
```

---

## 2. Multi-Turn Caller Verification Flow

```mermaid
sequenceDiagram
    autonumber
    actor Customer
    participant Agent as VoiceOps Agent
    participant OrderTool as Order Tool Gate
    participant DB as SQLite DB
    participant Ticket as Ticket Tool

    Customer->>Agent: "Hello, mujhe order ke baare mein help chahiye."
    Agent-->>Customer: "Hello! I am ZentroMart's AI assistant. Please share your order number."
    
    Customer->>Agent: "Order number hai 8978 2837."
    Agent->>OrderTool: lookup_order(89782837) [Unverified]
    OrderTool-->>Agent: {"verification_required": true} (No order details disclosed)
    Agent-->>Customer: "To protect your details, please share your registered phone last 4 digits or pincode."
    
    Customer->>Agent: "Aakhri 4 ank 4533 hain."
    Agent->>OrderTool: lookup_order(89782837, verification_value="4533")
    OrderTool->>DB: Query customer & order records
    DB-->>OrderTool: Valid match confirmed
    OrderTool-->>Agent: {"verified": true, "items": [...], "status": "delivered", ...}
    Agent-->>Customer: "Identity verified! How can I assist you with order 89782837?"
    
    Customer->>Agent: "Smart TV broken on delivery. Approve replacement now."
    Agent->>Agent: Check item value (> ₹10,000 threshold under DWM-3)
    Agent->>Ticket: create_ticket(summary="High-value damage claim...", reason="high_value_damage")
    Ticket-->>Agent: {"created": true, "ticket_id": "TKT..."}
    Agent-->>Customer: "High-value claims must be reviewed by Priority Resolution. I have created ticket TKT..."
```

---

## 3. Database Entity Relationship Diagram

```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    ORDERS ||--|{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : referenced_in
    PINCODES ||--o{ CUSTOMERS : resides_in
    PINCODES ||--o{ ORDERS : delivers_to
    ORDERS ||--o{ SUPPORT_LOGS : references
    CUSTOMERS ||--o{ SUPPORT_LOGS : customer_in
    ORDERS ||--o{ TICKETS : escalates

    CUSTOMERS {
        string customer_id PK
        string name
        string phone
        string email
        string pincode FK
        int is_plus
        string preferred_language
        string created_at
    }

    ORDERS {
        string order_id PK
        string customer_id FK
        string placed_at
        string status
        string delivery_pincode FK
        string promised_date
        string delivered_on
        int subtotal_inr
        int coupon_discount_inr
        int delivery_fee_inr
        int cod_fee_inr
        int total_inr
        string payment_method
        string return_status
        string refund_status
    }

    ORDER_ITEMS {
        string order_id PK,FK
        int line_no PK
        string sku FK
        string title
        string return_category
        int qty
        int unit_price_inr
    }

    PRODUCTS {
        string sku PK
        string title
        string brand
        string return_category
        int price_inr
        string fulfilled_by
        int assured
        int warranty_months
    }

    PINCODES {
        string pincode PK
        string city
        string state
        int serviceable
        int cod_available
        int express_available
    }

    HOLIDAYS {
        string date PK
        string name
    }

    TICKETS {
        string ticket_id PK
        string created_at
        string order_id FK
        string intent
        string reason
        string summary
        string status
    }
```

---

## 4. Key Security & Safety Guarantees
1. **Stateless Verification Gate**: Private customer order information is never returned until either the last 4 digits of the caller's registered phone number or the 6-digit delivery pincode is verified against the database.
2. **Session Memory Isolation**: Each conversation is keyed by a unique `conversation_id`. State, cached tokens, and verified orders never leak across sessions.
3. **Strict Policy Precedence**: Documents are ranked by legal and operational precedence (`policy` > `agent_guide` > `help` > `faq` > `marketing`), preventing outdated or generic marketing copy from overriding binding rules.
4. **No Model SQL/Code Execution**: All database operations use parameterized queries via dedicated repository functions. The LLM never writes or executes arbitrary code or SQL.
