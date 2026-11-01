"""
Native Windows SQLite Query Runner.
Executes queries.sql and prints formatted tables without external dependencies.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "operations.db"
QUERIES_PATH = BASE_DIR / "queries.sql"

def run_audits():
    if not DB_PATH.exists():
        print("[!] Database not found. Run ingest_to_db.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(QUERIES_PATH, "r", encoding="utf-8") as f:
        sql_content = f.read()

    raw_queries = [q.strip() for q in sql_content.split(";") if q.strip()]

    query_titles = [
        "Audit 1: Vendor Late-Fulfillment Rate Summary (Benchmark: 2026-10-31)",
        "Audit 2: Value of Overdue Open Orders (Benchmark: 2026-10-31)",
        "Audit 3: Missing Destination Postal Code Audit",
        "Audit 4: Non-Positive Line Item Quantity Audit (Active Orders Only)",
        "Audit 5: Reporting View Execution (v_vendor_performance_summary)"
    ]

    for title, query in zip(query_titles, raw_queries):
        print("\n" + "=" * 75)
        print(f"[*] {title}")
        print("=" * 75)
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            headers = [d[0] for d in cursor.description]

            col_widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
            header_line = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
            print(header_line)
            print("-" * len(header_line))

            for row in rows[:10]:
                print(" | ".join(f"{str(val):<{w}}" for val, w in zip(row, col_widths)))

            if len(rows) > 10:
                print(f"... [{len(rows) - 10} additional rows omitted]")

        except Exception as e:
            print(f"[!] Error executing query: {e}")

    conn.close()

if __name__ == "__main__":
    run_audits()