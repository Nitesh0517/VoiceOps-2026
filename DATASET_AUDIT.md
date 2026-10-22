# VoiceOps 2026 — Dataset Audit & Validation Report

## 1. Dataset Integrity & Offline Validation
The dataset was extracted from `Capstone_Project_Dataset_FTTT_2026.zip` and verified using `validate_dataset.py`.

```
================================================================================
VALIDATION RESULT: PASS
Verified: 9 CSVs, 21 KB documents, primary/foreign keys, order math,
          practice evidence, verification gates and company naming.
Counts:   1,000 orders | 1,783 items | 244 logs | 52 questions | 23 conversations
================================================================================
```

---

## 2. Relational Database Tables (`data/`)

### 2.1 `customers.csv` (300 rows)
* **Primary Key**: `customer_id` (String, e.g. `C100001` - `C100300`)
* **Foreign Keys**: `pincode` $\to$ `pincodes.pincode`
* **Schema**:
  | Column | Type | Nullable | Description / Business Meaning |
  |---|---|---|---|
  | `customer_id` | TEXT | No | Unique customer identifier |
  | `name` | TEXT | No | Full customer name |
  | `email` | TEXT | No | Synthetic customer email (`@example.com`) |
  | `phone` | TEXT | No | Phone number (`+91 5...` unallocated prefix) |
  | `pincode` | TEXT | No | Customer's registered postal code (6 digits) |
  | `is_plus` | BOOLEAN | No | ZentroMart Plus membership flag (`True`/`False`) |
  | `preferred_language` | TEXT | No | Preferred language (`en`, `hi`, `hi-en`, etc.) |
  | `created_at` | TEXT | No | Account registration ISO timestamp |

### 2.2 `orders.csv` (1,000 rows)
* **Primary Key**: `order_id` (TEXT, 8 digits, e.g. `10000001` - `99999999`)
* **Foreign Keys**: `customer_id` $\to$ `customers.customer_id`, `delivery_pincode` $\to$ `pincodes.pincode`
* **Schema**:
  | Column | Type | Nullable | Description |
  |---|---|---|---|
  | `order_id` | TEXT | No | Unique 8-digit order identifier |
  | `customer_id` | TEXT | No | FK referencing customer |
  | `order_date` | TEXT | No | Order placement date (YYYY-MM-DD) |
  | `status` | TEXT | No | Status (`placed`, `shipped`, `delivered`, `cancelled`, `rto`) |
  | `delivery_pincode` | TEXT | No | 6-digit delivery pincode |
  | `promised_date` | TEXT | No | Guaranteed delivery date |
  | `delivered_date` | TEXT | Yes | Actual delivery date (empty if not delivered) |
  | `subtotal_inr` | INTEGER | No | Sum of line items ($qty \times unit\_price$) |
  | `coupon_discount_inr` | INTEGER | Yes | Applied discount amount |
  | `delivery_fee_inr` | INTEGER | No | Delivery fee charged |
  | `cod_fee_inr` | INTEGER | No | Cash-on-delivery handling fee |
  | `total_inr` | INTEGER | No | Final billed amount ($subtotal - discount + delivery + cod$) |
  | `payment_method` | TEXT | No | Payment type (`upi`, `credit_card`, `debit_card`, `wallet`, `cod`, `netbanking`) |
  | `return_status` | TEXT | Yes | Return stage (`requested`, `pickup_scheduled`, `received`, `rejected`, `completed`) |
  | `refund_status` | TEXT | Yes | Refund stage (`pending`, `processed`, `failed`) |
  | `refund_amount_inr` | INTEGER | Yes | Billed refund amount |

### 2.3 `order_items.csv` (1,783 rows)
* **Primary Key**: Composite `(order_id, line_no)`
* **Foreign Keys**: `order_id` $\to$ `orders.order_id`, `sku` $\to$ `products.sku`
* **Schema**:
  | Column | Type | Nullable | Description |
  |---|---|---|---|
  | `order_id` | TEXT | No | FK referencing order |
  | `line_no` | INTEGER | No | Line item number within order |
  | `sku` | TEXT | No | Product stock keeping unit (e.g. `ELE-0001`, `GRO-0010`) |
  | `title` | TEXT | No | Product title |
  | `qty` | INTEGER | No | Quantity ordered |
  | `unit_price_inr` | INTEGER | No | Price per unit |
  | `return_category` | TEXT | No | Category governing return window & condition |

### 2.4 `products.csv` (70 rows)
* **Primary Key**: `sku` (TEXT)
* **Schema**:
  | Column | Type | Description |
  |---|---|---|
  | `sku` | TEXT | Unique product SKU |
  | `title` | TEXT | Product name |
  | `category` | TEXT | Main category (`Electronics`, `Groceries`, `Apparel`, `Beauty`, `Home`) |
  | `return_category` | TEXT | Rules group (`electronics_standard`, `apparel`, `grocery_fresh`, `beauty`, etc.) |
  | `price_inr` | INTEGER | Retail listing price |
  | `fulfilled_by` | TEXT | `ZentroMart` vs `Marketplace Seller` |
  | `assured` | BOOLEAN | ZentroMart Assured quality certified (`True`/`False`) |
  | `warranty_months` | INTEGER | Warranty duration in months |

### 2.5 `pincodes.csv` (36 rows)
* **Primary Key**: `pincode` (TEXT, 6 digits)
* **Columns**: `pincode`, `city`, `state`, `serviceable` (`True`/`False`), `cod_available` (`True`/`False`), `express_available` (`True`/`False`).

### 2.6 `holidays.csv` (4 rows)
* **Primary Key**: `date` (YYYY-MM-DD)
* **Calendar Dates**:
  - `2026-08-15` (Independence Day)
  - `2026-10-02` (Gandhi Jayanti)
  - `2026-10-19` (Warehouse closure - festival)
  - `2026-11-09` (Warehouse closure - festival)
* **Business Day Rule**: Business days are Monday through Saturday, **excluding** these 4 dates.

### 2.7 `support_logs.csv` (244 rows)
* **Primary Key**: `log_id`
* **Columns**: `log_id`, `customer_id`, `order_id`, `created_at`, `channel`, `intent`, `resolution`, `transcript`.
* **Note**: Historical transcripts only. Used for domain vocabulary learning; **never** treated as policy authority.

---

## 3. Knowledge Base Inventory (`kb/` — 21 Documents)

| Document | Type | Status | Effective Date | Main Topics & Key Section IDs |
|---|---|---|---|---|
| `00_about_this_knowledge_base.md` | meta | current | 2026-08-01 | Precedence rules (`KB-00.1`), Reference date (`KB-00.2`), Business days (`KB-00.3`) |
| `agent_conversation_style.md` | agent_guide | current | 2026-08-01 | Assistant persona (`STY-1`), AI self-introduction, tone, brevity |
| `agent_escalation_handoff.md` | agent_guide | current | 2026-08-01 | Escalation triggers (`ESC-1` to `ESC-4`), Priority team handoff |
| `agent_identity_verification.md` | agent_guide | current | 2026-08-01 | Identity verification protocol (`IDV-1` to `IDV-3`), caller verification gates |
| `faq_general.md` | faq | current | 2026-08-01 | Generic FAQ answers (`FAQ-1` to `FAQ-6`) |
| `faq_hindi.md` | faq | current | 2026-08-01 | Hindi-language common questions (`FAQ-HI-1` to `FAQ-HI-6`) |
| `help_reverse_pickup.md` | help | current | 2026-08-01 | Reverse courier scheduling & requirements (`RPK-1` to `RPK-4`) |
| `help_track_order.md` | help | current | 2026-08-01 | Tracking status explanations (`TRK-1` to `TRK-4`) |
| `help_troubleshooting_electronics.md` | help | current | 2026-08-01 | Self-service troubleshooting before return (`TRB-1` to `TRB-3`) |
| `mkt_plus_benefits_page.md` | marketing | current | 2026-08-01 | Marketing summary of Plus tier (`MKT-PLS-1`) |
| `pol_cancellations.md` | policy | current | 2026-08-01 | Order cancellation windows (`CAN-1` to `CAN-4`) |
| `pol_coupons_offers.md` | policy | current | 2026-08-01 | Promotional code terms (`CPN-1` to `CPN-3`) |
| `pol_damaged_wrong_missing.md` | policy | current | 2026-08-01 | Damaged/wrong item policy (`DWM-1` to `DWM-5`), 48hr window, photos |
| `pol_delivery_shipping.md` | policy | current | 2026-08-01 | Shipping charges, express timelines (`DEL-1` to `DEL-5`) |
| `pol_marketplace_sellers.md` | policy | current | 2026-08-01 | Third-party seller return constraints (`MKT-1` to `MKT-3`) |
| `pol_payments_cod.md` | policy | current | 2026-08-01 | Cash on delivery rules and limits (`PAY-1` to `PAY-4`) |
| `pol_plus_membership.md` | policy | current | 2026-08-01 | Formal Plus terms, free return pickup (`PLS-1` to `PLS-4`) |
| `pol_refunds.md` | policy | current | 2026-08-01 | Refund methods and business-day timelines (`REF-1` to `REF-5`) |
| `pol_returns_v4.md` | policy | current | 2026-08-01 | Current return policy (`RET-1` to `RET-9`), category windows, fees |
| `pol_returns_v3_superseded.md` | policy | superseded | 2026-01-01 | Superseded return policy (retained for backward reference) |
| `pol_warranty_repairs.md` | policy | current | 2026-08-01 | Warranty coverage, brand vs Assured (`WAR-1` to `WAR-4`) |

---

## 4. Practice Evaluation Datasets (`practice/`)

### 4.1 `practice/questions.csv` (52 single-turn test cases)
* **Columns**: `id`, `language`, `question`, `asr_text`, `intent`, `expected_decision`, `acceptable_decisions`, `answerable`, `gold_evidence`, `hard_negatives`, `must_include`, `must_not_include`, `reference_answer`, `reply_language`, `entities`, `notes`, `needs_native_review`.
* **Key Scenarios Tested**:
  - Grounded factual policy answers (`return_fee`, `refund_timeline`, `warranty`).
  - Catalog lookups (`products.csv:<sku>` joining policy).
  - Unanswerable/unsupported questions (`answerable == False`) $\to$ must decline politely without hallucination.
  - Policy vs FAQ conflict traps (e.g. Wallet refund instant in `pol_refunds.md` vs 5-7 days in `faq_general.md`).
  - Superseded policy traps (`pol_returns_v4.md` current vs `v3` superseded).
  - Multilingual evaluation: English (`en`), Hindi (`hi`), and Hinglish (`hi-en`).

### 4.2 `practice/conversations.csv` (23 conversations, 96 turns)
* **Columns**: `conversation_id`, `turn`, `scenario`, `language`, `order_id`, `customer_id`, `customer_message`, `expected_decision`, `must_include`, `must_not_include`, `expected_tool_calls`, `gold_evidence`, `notes`.
* **Verification & Memory Flow**:
  1. Turn 1: Caller asks for order help $\to$ AI greets, states it is an AI assistant, asks for order ID.
  2. Turn 2: Caller gives order ID $\to$ AI invokes unverified `lookup_order(order_id)` $\to$ asks for phone last 4 digits or pincode.
  3. Turn 3: Caller gives 4 or 6 digits $\to$ AI invokes verified `lookup_order(order_id, verification_value=...)` $\to$ confirms verification.
  4. Subsequent turns: Answers order-specific inquiries, evaluates return windows against 2026-10-20 reference date, handles escalations (`create_ticket`), and resolves coreferences.

---

## 5. Tool Specifications & Safety Gates

### 5.1 `lookup_order(order_id: str, verification_value: str = None) -> dict`
* **Stateless gate**:
  - `verification_value is None` $\to$ returns `{"verification_required": True, "order_id": ...}` with zero customer or order data.
  - `verification_value == phone[-4:]` OR `delivery_pincode` $\to$ returns `{"found": True, "verified": True, ...order details, "items": [...]}`.
  - Invalid proof $\to$ returns `{"verified": False, "verification_required": True}`.

### 5.2 `create_ticket(summary: str, order_id: str = None, reason: str = None, intent: str = None) -> dict`
* Minimum summary length requirement: $\ge 20$ characters.
* Success condition: Appends to `tools/tickets_created.csv` and returns `{"created": True, "ticket_id": "TKT..."}`.
