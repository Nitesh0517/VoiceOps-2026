"""Support ticket creation tool matching official specification."""
import os
import csv
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, Optional
from app.config import settings
from app.database.repository import DatabaseRepository


class TicketTool:
    def __init__(self, repo: Optional[DatabaseRepository] = None):
        self.repo = repo or DatabaseRepository()
        self.csv_path = settings.BASE_DIR / "tools" / "tickets_created.csv"
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

    def create_ticket(self, summary: str, order_id: Optional[str] = None,
                      reason: Optional[str] = None, intent: Optional[str] = None) -> Dict[str, Any]:
        """
        Log a synthetic human-handover ticket.
        Requires summary >= 20 characters.
        """
        if not summary or len(summary.strip()) < 20:
            return {
                "created": False,
                "error": "summary too short: include issue, checks made, and escalation reason"
            }
            
        tid = "TKT" + uuid4().hex
        now = datetime.now().isoformat(timespec="seconds")
        oid = "".join(ch for ch in str(order_id) if "0" <= ch <= "9") if order_id else ""
        
        # 1. Log to SQLite
        self.repo.create_ticket(summary=summary, order_id=oid or None, reason=reason, intent=intent)
        
        # 2. Append to CSV for compatibility
        row = {
            "ticket_id": tid,
            "created_at": now,
            "order_id": oid,
            "intent": intent or "",
            "reason": reason or "",
            "summary": summary.strip()
        }
        fresh = not self.csv_path.exists()
        with open(self.csv_path, "a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
            if fresh:
                writer.writeheader()
            writer.writerow(row)
            
        return {
            "created": True,
            "ticket_id": tid
        }
