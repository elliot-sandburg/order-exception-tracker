"""
ETL Pipeline: Normalizes orders_raw.csv into 3NF SQLite database.
- Enforces 1-row-per-order demonstration assumption.
- Normalizes identifiers before duplicate quarantine.
- Full transactional safety with rollback and explicit count assertions.
"""

import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
CSV_PATH = REPO_DIR / "orders_raw.csv"
DB_PATH = BASE_DIR / "operations.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
QUARANTINE_PATH = BASE_DIR / "quarantined_duplicates.csv"

def initialize_database():
    print(f"[*] Initializing SQLite database schema at: {DB_PATH.name}")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

def ingest_data():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"[!] Source dataset not found at: {CSV_PATH}")

    print(f"[*] Reading source dataset: {CSV_PATH.name}")
    df = pd.read_csv(
        CSV_PATH, 
        dtype={"order_id": str, "shipping_zip": str, "vendor_name": str, "customer_name": str},
        keep_default_na=False
    )
    df.columns = [c.strip().lower() for c in df.columns]
    source_row_count = len(df)

    # 1. Normalize fields BEFORE checking duplicates
    df["order_id"] = df["order_id"].astype(str).str.strip()
    df["vendor_name"] = df["vendor_name"].astype(str).str.strip()
    df["customer_name"] = df["customer_name"].astype(str).str.strip()
    df["status"] = df["status"].astype(str).str.strip().str.capitalize()

    if (df["order_id"] == "").any():
        raise ValueError("[!] Blank order IDs detected; resolve source data before ingestion.")
    if (df["vendor_name"] == "").any():
        raise ValueError("[!] Missing vendor names detected; resolve source data before ingestion.")

    # 2. Quarantine colliding duplicate Order IDs
    dup_mask = df.duplicated(subset=["order_id"], keep=False)
    quarantine_df = df[dup_mask]
    clean_df = df[~dup_mask]

    # Always overwrite quarantine file (even if empty) to prevent stale state
    quarantine_df.to_csv(QUARANTINE_PATH, index=False)
    print(f"[*] Quarantined {len(quarantine_df)} colliding duplicate rows to: {QUARANTINE_PATH.name}")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        # 3. Ingest VENDORS (From clean records only)
        print("[*] Ingesting vendors table...")
        clean_vendors = sorted([v for v in clean_df["vendor_name"].unique() if v])
        vendor_map = {}
        for idx, v_name in enumerate(clean_vendors, start=1):
            v_id = f"VND-{idx:03d}"
            vendor_map[v_name] = v_id
            cursor.execute(
                """
                INSERT OR IGNORE INTO vendors (vendor_id, vendor_name, lead_time_days, status)
                VALUES (?, ?, 7, 'Active')
                """,
                (v_id, v_name)
            )

        # 4. Ingest ORDERS (Non-conflicting orders only)
        print("[*] Ingesting non-conflicting purchase orders...")
        for _, row in clean_df.iterrows():
            v_id = vendor_map.get(row["vendor_name"])
            zip_val = row["shipping_zip"].strip() if row["shipping_zip"].strip() else None
            cursor.execute(
                """
                INSERT INTO orders (
                    order_id, customer_name, vendor_id, order_date, 
                    expected_delivery, shipping_zip, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["order_id"], row["customer_name"], v_id, 
                    row["order_date"].strip(), row["expected_delivery"].strip(), 
                    zip_val, row["status"]
                )
            )

        # 5. Ingest ORDER_ITEMS (One line item per clean order row)
        print("[*] Ingesting non-conflicting line items...")
        for _, row in clean_df.iterrows():
            cursor.execute(
                """
                INSERT INTO order_items (order_id, quantity, unit_price)
                VALUES (?, ?, ?)
                """,
                (
                    row["order_id"], 
                    int(row["quantity"]), 
                    float(row["unit_price"])
                )
            )

        # 6. Explicit Reconciliation Validation BEFORE Commit
        v_count = cursor.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
        o_count = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        i_count = cursor.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]

        expected_loaded = len(clean_df)

        if source_row_count != len(quarantine_df) + expected_loaded:
            raise RuntimeError(f"Reconciliation error: {source_row_count} source != {len(quarantine_df)} quarantined + {expected_loaded} clean.")

        if o_count != expected_loaded or i_count != expected_loaded:
            raise RuntimeError(f"Database row count mismatch: orders ({o_count}) or items ({i_count}) != expected ({expected_loaded}).")

        # Commit only after all checks pass
        conn.commit()

        print("\n" + "=" * 55)
        print("  RECONCILIATION SUMMARY")
        print("=" * 55)
        print(f"    Total Source Rows:       {source_row_count}")
        print(f"  - Quarantined Collisions:  {len(quarantine_df)} (Exported to CSV)")
        print(f"  = Loaded Non-Conflicting:  {o_count}")
        print(f"    Line Items Loaded:       {i_count}")
        print(f"    Active Vendors:          {v_count}")
        print("=" * 55)
        print("[+] Row-count reconciliation passed.\n")

    except Exception as e:
        conn.rollback()
        print(f"\n[!] INGESTION FAILED - Transaction rolled back: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()
    ingest_data()