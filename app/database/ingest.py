"""Data ingestion pipeline from CSV tables to SQLite."""
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List
from app.config import settings
from app.database.connection import init_db, get_db_connection

logger = logging.getLogger(__name__)

TEXT_COLS = {
    "order_id", "customer_id", "delivery_pincode", "return_rrn",
    "cancellation_rrn", "rto_rrn", "sku", "return_sku", "damage_sku",
    "pincode", "phone", "coupon_code"
}


def _clean_val(key: str, val: str) -> Any:
    val = val.strip()
    if val == "":
        return None
    if val in ("True", "true"):
        return 1
    if val in ("False", "false"):
        return 0
    if key in TEXT_COLS:
        return val
    if val.lstrip("-").isdigit():
        return int(val)
    return val


def read_csv_clean(filepath: Path) -> List[Dict[str, Any]]:
    with open(filepath, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [{k: _clean_val(k, v) for k, v in row.items()} for row in reader]


def ingest_table(cursor, table_name: str, rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 0
    cols = list(rows[0].keys())
    col_str = ", ".join(cols)
    placeholders = ", ".join(f":{c}" for c in cols)
    sql = f"INSERT OR REPLACE INTO {table_name} ({col_str}) VALUES ({placeholders})"
    cursor.executemany(sql, rows)
    return len(rows)


def ingest_all_data(data_dir: Path | None = None, db_path: Path | None = None) -> Dict[str, int]:
    """Ingest all 7 CSV files into SQLite database."""
    source_dir = data_dir or settings.DATA_CSV_DIR
    init_db(db_path)
    
    counts: Dict[str, int] = {}
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Order of tables matters for Foreign Keys:
        # 1. pincodes
        pincodes = read_csv_clean(source_dir / "pincodes.csv")
        counts["pincodes"] = ingest_table(cursor, "pincodes", pincodes)
        
        # 2. holidays
        holidays = read_csv_clean(source_dir / "holidays.csv")
        counts["holidays"] = ingest_table(cursor, "holidays", holidays)

        # 3. customers (FK -> pincodes)
        customers = read_csv_clean(source_dir / "customers.csv")
        counts["customers"] = ingest_table(cursor, "customers", customers)

        # 4. products
        products = read_csv_clean(source_dir / "products.csv")
        counts["products"] = ingest_table(cursor, "products", products)

        # 5. orders (FK -> customers, pincodes)
        orders = read_csv_clean(source_dir / "orders.csv")
        counts["orders"] = ingest_table(cursor, "orders", orders)

        # 6. order_items (FK -> orders, products)
        order_items = read_csv_clean(source_dir / "order_items.csv")
        counts["order_items"] = ingest_table(cursor, "order_items", order_items)

        # 7. support_logs (FK -> customers, orders)
        support_logs = read_csv_clean(source_dir / "support_logs.csv")
        counts["support_logs"] = ingest_table(cursor, "support_logs", support_logs)

        conn.commit()
    
    logger.info(f"Ingested data counts: {counts}")
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = ingest_all_data()
    print("Ingestion complete:", res)
