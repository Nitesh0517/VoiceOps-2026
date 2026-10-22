"""Database schema definitions for ZentroMart matching all CSV columns exactly."""

CREATE_TABLES_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS pincodes (
    pincode TEXT PRIMARY KEY,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    metro INTEGER,
    serviceable INTEGER NOT NULL,
    cod_available INTEGER NOT NULL,
    express_available INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    city TEXT,
    state TEXT,
    pincode TEXT NOT NULL,
    is_plus INTEGER NOT NULL,
    plus_since TEXT,
    preferred_language TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (pincode) REFERENCES pincodes(pincode)
);

CREATE TABLE IF NOT EXISTS products (
    sku TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    brand TEXT,
    return_category TEXT NOT NULL,
    price_inr INTEGER NOT NULL,
    fulfilled_by TEXT NOT NULL,
    assured INTEGER NOT NULL,
    warranty_months INTEGER NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    placed_at TEXT NOT NULL,
    status TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    delivery_type TEXT,
    delivery_pincode TEXT NOT NULL,
    promised_date TEXT NOT NULL,
    shipped_on TEXT,
    delivered_on TEXT,
    delivery_attempts INTEGER,
    subtotal_inr INTEGER NOT NULL,
    coupon_code TEXT,
    coupon_discount_inr INTEGER,
    coupon_min_order_inr INTEGER,
    delivery_fee_inr INTEGER NOT NULL,
    cod_fee_inr INTEGER NOT NULL,
    total_inr INTEGER NOT NULL,
    contacts_last_7_days INTEGER,
    cancellation_refund_initiated_on TEXT,
    cancellation_refund_method TEXT,
    cancellation_refund_amount_inr INTEGER,
    cancellation_rrn TEXT,
    rto_refund_initiated_on TEXT,
    rto_refund_method TEXT,
    rto_refund_amount_inr INTEGER,
    rto_rrn TEXT,
    express_late_credit_inr INTEGER,
    express_late_credit_on TEXT,
    return_sku TEXT,
    return_line_no INTEGER,
    return_qty INTEGER,
    return_reason TEXT,
    return_status TEXT,
    return_requested_on TEXT,
    return_pickup_on TEXT,
    return_qc_passed_on TEXT,
    return_refund_initiated_on TEXT,
    return_refund_method TEXT,
    return_refund_amount_inr INTEGER,
    return_refund_completed_on TEXT,
    return_rrn TEXT,
    return_reverse_pickup_fee_inr INTEGER,
    damage_sku TEXT,
    damage_issue TEXT,
    damage_reported_at TEXT,
    damage_hours_after_delivery INTEGER,
    damage_photos_attached INTEGER,
    damage_status TEXT,
    timeline TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (delivery_pincode) REFERENCES pincodes(pincode)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id TEXT NOT NULL,
    line_no INTEGER NOT NULL,
    sku TEXT NOT NULL,
    title TEXT NOT NULL,
    return_category TEXT NOT NULL,
    qty INTEGER NOT NULL,
    unit_price_inr INTEGER NOT NULL,
    PRIMARY KEY (order_id, line_no),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (sku) REFERENCES products(sku)
);

CREATE TABLE IF NOT EXISTS holidays (
    date TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS support_logs (
    log_id TEXT PRIMARY KEY,
    channel TEXT,
    started_at TEXT,
    language TEXT,
    customer_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    intent TEXT,
    handled_by TEXT,
    transcript TEXT NOT NULL,
    resolution TEXT,
    escalated INTEGER,
    csat INTEGER,
    qa_reviewed INTEGER,
    qa_findings TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    order_id TEXT,
    intent TEXT,
    reason TEXT,
    summary TEXT NOT NULL,
    status TEXT DEFAULT 'open'
);
"""
