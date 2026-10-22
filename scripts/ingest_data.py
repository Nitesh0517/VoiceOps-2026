#!/usr/bin/env python3
"""CLI script to ingest CSV tables into SQLite database."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.ingest import ingest_all_data

if __name__ == "__main__":
    print("Ingesting ZentroMart datasets into SQLite...")
    counts = ingest_all_data()
    print("Ingestion complete successfully!")
    for table, count in counts.items():
        print(f"  - {table}: {count} rows")
