"""Database repository providing verified lookups and query helpers."""
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4
from app.database.connection import get_db_connection


class DatabaseRepository:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM customers WHERE customer_id = ?",
                (str(customer_id).strip(),)
            ).fetchone()
            return dict(row) if row else None

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        oid = "".join(ch for ch in str(order_id) if "0" <= ch <= "9")
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM orders WHERE order_id = ?",
                (oid,)
            ).fetchone()
            return dict(row) if row else None

    def get_order_items(self, order_id: str) -> List[Dict[str, Any]]:
        oid = "".join(ch for ch in str(order_id) if "0" <= ch <= "9")
        with get_db_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM order_items WHERE order_id = ? ORDER BY line_no ASC",
                (oid,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_product(self, sku: str) -> Optional[Dict[str, Any]]:
        sku_clean = str(sku).strip().upper()
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE sku = ?",
                (sku_clean,)
            ).fetchone()
            return dict(row) if row else None

    def get_product_by_name(self, query: str) -> Optional[Dict[str, Any]]:
        q = f"%{query.strip()}%"
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM products WHERE title LIKE ? OR sku LIKE ? LIMIT 1",
                (q, q)
            ).fetchone()
            return dict(row) if row else None

    def get_pincode(self, pincode: str) -> Optional[Dict[str, Any]]:
        pin = "".join(ch for ch in str(pincode) if "0" <= ch <= "9")
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM pincodes WHERE pincode = ?",
                (pin,)
            ).fetchone()
            return dict(row) if row else None

    def get_holidays(self) -> List[Dict[str, str]]:
        with get_db_connection(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM holidays ORDER BY date ASC").fetchall()
            return [dict(r) for r in rows]

    def create_ticket(self, summary: str, order_id: Optional[str] = None,
                      reason: Optional[str] = None, intent: Optional[str] = None) -> Dict[str, Any]:
        """Create support ticket with validation."""
        if not summary or len(summary.strip()) < 20:
            return {
                "created": False,
                "error": "summary too short: include issue, checks made, and escalation reason"
            }
        tid = "TKT" + uuid4().hex
        now = datetime.now().isoformat(timespec="seconds")
        oid = "".join(ch for ch in str(order_id) if "0" <= ch <= "9") if order_id else None
        
        with get_db_connection(self.db_path) as conn:
            conn.execute(
                """INSERT INTO tickets (ticket_id, created_at, order_id, intent, reason, summary, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'open')""",
                (tid, now, oid, intent or "", reason or "", summary.strip())
            )
            conn.commit()
            
        return {
            "created": True,
            "ticket_id": tid,
            "created_at": now,
            "order_id": oid,
            "summary": summary.strip()
        }

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        with get_db_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM tickets WHERE ticket_id = ?",
                (ticket_id.strip(),)
            ).fetchone()
            return dict(row) if row else None
