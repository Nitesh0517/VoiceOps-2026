"""Automated tests for database setup and repository lookups."""
import pytest
from pathlib import Path
from app.config import settings
from app.database.connection import init_db, get_db_connection
from app.database.ingest import ingest_all_data
from app.database.repository import DatabaseRepository


@pytest.fixture(scope="module")
def repo():
    test_db = settings.BASE_DIR / "data" / "test_zentromart.db"
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass
    ingest_all_data(db_path=test_db)
    yield DatabaseRepository(db_path=test_db)
    import gc
    gc.collect()
    if test_db.exists():
        try:
            test_db.unlink()
        except Exception:
            pass


def test_database_counts(repo):
    with get_db_connection(repo.db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 300
        assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 1000
        assert conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 1783
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 70
        assert conn.execute("SELECT COUNT(*) FROM pincodes").fetchone()[0] == 36
        assert conn.execute("SELECT COUNT(*) FROM holidays").fetchone()[0] == 4
        assert conn.execute("SELECT COUNT(*) FROM support_logs").fetchone()[0] == 244


def test_order_math(repo):
    with get_db_connection(repo.db_path) as conn:
        orders = conn.execute("SELECT * FROM orders").fetchall()
        for ord in orders:
            subtotal = ord["subtotal_inr"]
            discount = ord["coupon_discount_inr"] or 0
            deliv = ord["delivery_fee_inr"]
            cod = ord["cod_fee_inr"]
            expected_total = subtotal - discount + deliv + cod
            assert ord["total_inr"] == expected_total


def test_customer_and_order_lookup(repo):
    order = repo.get_order("89782837")
    assert order is not None
    assert order["customer_id"] == "C100181"
    
    customer = repo.get_customer(order["customer_id"])
    assert customer is not None
    assert customer["phone"][-4:] == "4533"
    assert order["delivery_pincode"] == "781006"
    
    items = repo.get_order_items("89782837")
    assert len(items) >= 1
    assert any("TV" in it["title"] for it in items)


def test_ticket_creation(repo):
    # Short summary should fail
    fail = repo.create_ticket("short")
    assert fail["created"] is False
    
    # Valid summary should succeed
    succ = repo.create_ticket(
        summary="Customer reports broken screen on 43-inch TV. Requesting priority replacement.",
        order_id="89782837",
        reason="high_value_damage",
        intent="damage"
    )
    assert succ["created"] is True
    assert succ["ticket_id"].startswith("TKT")
    
    # Verify retrieval
    tkt = repo.get_ticket(succ["ticket_id"])
    assert tkt is not None
    assert tkt["order_id"] == "89782837"
