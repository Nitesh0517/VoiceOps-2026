#!/usr/bin/env python3
"""Dataset Inspection & Summary Tool."""
import glob
import csv
from pathlib import Path
from app.config import settings

def inspect():
    print("=" * 60)
    print("        ZENTROMART DATASET INSPECTION SUMMARY        ")
    print("=" * 60)
    print(f"Reference Date: {settings.REFERENCE_DATE}\n")

    print("[CSV Tables]")
    for p in sorted(glob.glob(str(settings.DATA_CSV_DIR / "*.csv"))):
        with open(p, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = sum(1 for _ in reader)
            name = Path(p).name
            print(f"  {name:20} -> {rows:5} rows | {len(header)} cols")

    print("\n[Knowledge Base Documents]")
    md_files = sorted(glob.glob(str(settings.KB_DIR / "*.md")))
    print(f"  Total KB Files: {len(md_files)}")
    for p in md_files:
        name = Path(p).name
        size = Path(p).stat().st_size
        print(f"  {name:35} ({size:5} bytes)")

    print("\n[Practice Evaluation Sets]")
    for p in sorted(glob.glob(str(settings.PRACTICE_DIR / "*.csv"))):
        with open(p, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = sum(1 for _ in reader)
            name = Path(p).name
            print(f"  {name:20} -> {rows:5} rows | {len(header)} cols")

    print("=" * 60)

if __name__ == "__main__":
    inspect()
