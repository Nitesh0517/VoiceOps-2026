"""Deterministic business rules and calendar calculators for ZentroMart."""
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple

REFERENCE_DATE = date(2026, 10, 20)

WAREHOUSE_HOLIDAYS = {
    date(2026, 8, 15),
    date(2026, 10, 2),
    date(2026, 10, 19),
    date(2026, 11, 9)
}

RETURN_WINDOWS_DAYS = {
    "grocery_fresh": 2,
    "grocery_staples": 5,
    "electronics": 7,
    "electronics_standard": 7,
    "appliances": 10,
    "apparel": 15,
    "clothing": 30,
    "footwear": 15,
    "beauty": 7,
    "home": 10
}

REFUND_BUSINESS_DAYS = {
    "wallet": (0, 0),       # Instant / within 2 hours
    "upi": (1, 3),          # 1 to 3 business days
    "credit_card": (5, 7),  # 5 to 7 business days
    "debit_card": (5, 7),   # 5 to 7 business days
    "netbanking": (5, 7),   # 5 to 7 business days
    "cod": (2, 4)           # 2 to 4 business days after NEFT
}


def is_business_day(d: date) -> bool:
    # Monday=0 ... Saturday=5, Sunday=6
    if d.weekday() == 6:  # Sunday is not a business day
        return False
    if d in WAREHOUSE_HOLIDAYS:
        return False
    return True


def add_business_days(start_date: date, n_days: int) -> date:
    """Add N business days, skipping Sundays and warehouse holidays."""
    cur = start_date
    added = 0
    while added < n_days:
        cur += timedelta(days=1)
        if is_business_day(cur):
            added += 1
    return cur


def calculate_refund_timeline(payment_method: str, start_date: date | None = None) -> Dict[str, Any]:
    pm = (payment_method or "").lower().strip()
    s_date = start_date or REFERENCE_DATE
    
    if "wallet" in pm:
        return {
            "method": "wallet",
            "description": "Instant, within 2 hours of initiation.",
            "min_days": 0,
            "max_days": 0,
            "deadline_date": s_date.isoformat()
        }
        
    min_days, max_days = REFUND_BUSINESS_DAYS.get(pm, (5, 7))
    min_date = add_business_days(s_date, min_days)
    max_date = add_business_days(s_date, max_days)
    
    return {
        "method": pm,
        "description": f"{min_days} to {max_days} business days",
        "min_date": min_date.isoformat(),
        "max_date": max_date.isoformat(),
        "deadline_date": max_date.isoformat()
    }


def calculate_return_window(delivered_on_str: str, return_category: str, is_plus: bool = False) -> Dict[str, Any]:
    """Calculate return deadline from delivery date in calendar days."""
    try:
        deliv_date = datetime.strptime(delivered_on_str.strip(), "%Y-%m-%d").date()
    except Exception:
        return {"eligible": False, "reason": "Invalid or missing delivery date"}
        
    cat = (return_category or "").lower().strip()
    # Apparel window: 30 days for clothing / some apparel; 15 days for standard
    if "jeans" in cat or "clothing" in cat or cat == "apparel":
        window = 30 if "clothing" in cat or "jeans" in cat else 15
    else:
        window = RETURN_WINDOWS_DAYS.get(cat, 7)
        
    deadline = deliv_date + timedelta(days=window)
    eligible = deadline >= REFERENCE_DATE
    
    return {
        "delivered_date": deliv_date.isoformat(),
        "return_window_days": window,
        "deadline_date": deadline.isoformat(),
        "eligible": eligible,
        "days_left": (deadline - REFERENCE_DATE).days if eligible else 0
    }


def calculate_pickup_fee(is_plus: bool, is_damaged_or_wrong: bool = False) -> int:
    """Return reverse pickup fee in INR."""
    if is_plus or is_damaged_or_wrong:
        return 0
    return 49
