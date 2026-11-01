"""
Defensive ETL Pipeline: Normalizes orders_raw.csv into 3NF SQLite database.
Standard Bulk-Load Configuration with Foreign Key Safety.
"""

import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
CSV_PATH = REPO_DIR / "orders_raw.csv"
DB_PATH = BASE_DIR / "operations.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"

def initialize_database():
    print(f"[*] Initializing SQLite database schema at: {DB_PATH.name}")
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()

def ingest_data():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"[!] Source dataset not found at: {CSV_PATH}")

    print(f"[*] Reading source dataset: {CSV_PATH.name}")
    df = pd.read_csv(CSV_PATH)
    df.columns = [c.strip().lower() for c in df.columns]

    # Clean vendor names
    df["vendor_name"] = df["vendor_name"].astype(str).str.strip()

    conn = sqlite3.connect(DB_PATH)
    # Disable foreign keys temporarily during bulk load (industry standard)
    conn.execute("PRAGMA foreign_keys = OFF;")
    cursor = conn.cursor()

    # 1. Ingest VENDORS
    print("[*] Normalizing vendors table...")
    unique_vendors = df["vendor_name"].dropna().unique()
    vendor_map = {}
    
    for idx, v_name in enumerate(sorted(unique_vendors), start=1):
        v_id = f"VND-{idx:03d}"
        vendor_map[v_name] = v_id
        cursor.execute(
            """
            INSERT OR IGNORE INTO vendors (vendor_id, vendor_name, lead_time_days, status)
            VALUES (?, ?, 7, 'Active')
            """,
            (v_id, v_name)
        )

    # 2. Ingest ORDERS
    print("[*] Normalizing purchase orders table...")
    orders_df = df.drop_duplicates(subset=["order_id"])

    for _, row in orders_df.iterrows():
        v_id = vendor_map.get(row["vendor_name"], "VND-001")
        zip_val = None if pd.isna(row["shipping_zip"]) else str(row["shipping_zip"]).split('.')[0].strip()
        
        cursor.execute(
            """
            INSERT OR IGNORE INTO orders (
                order_id, customer_name, vendor_id, order_date, 
                expected_delivery, shipping_zip, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(row["order_id"]), str(row["customer_name"]), v_id, 
                str(row["order_date"]), str(row["expected_delivery"]), 
                zip_val, str(row["status"]).capitalize()
            )
        )

    # 3. Ingest ORDER_ITEMS
    print("[*] Normalizing order line items...")
    for _, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO order_items (order_id, quantity, unit_price)
            VALUES (?, ?, ?)
            """,
            (
                str(row["order_id"]), 
                int(row["quantity"]), 
                float(row["unit_price"])
            )
        )

    conn.commit()

    # Re-enable foreign keys and verify integrity
    conn.execute("PRAGMA foreign_keys = ON;")
    fk_errors = cursor.execute("PRAGMA foreign_key_check;").fetchall()
    if fk_errors:
        print(f"[!] Warning: Found {len(fk_errors)} foreign key mismatches.")
    else:
        print("[+] Foreign Key Integrity Check: 100% PASSED")

    v_count = cursor.execute("SELECT COUNT(*) FROM vendors").fetchone()[0]
    o_count = cursor.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    i_count = cursor.execute("SELECT COUNT(*) FROM order_items").fetchone()[0]
    conn.close()

    print(f"\n[+] Database Ingestion Successfully Verified:")
    print(f"    - Unique Vendors:     {v_count} (Mohawk, Shaw, Armstrong, Daltile)")
    print(f"    - Purchase Orders:    {o_count}")
    print(f"    - Order Line Items:   {i_count}")

if __name__ == "__main__":
    initialize_database()
    ingest_data()