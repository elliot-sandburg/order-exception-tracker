# Retail Order-Exception & Fulfillment Validation Pipeline

A portfolio project modeling contractor order management, vendor logistics, and exception auditing in building materials distribution.

## 📊 Multi-Tab Discrepancy Report Preview
### Itemized Exceptions
![Itemized Exceptions](<Itemized Exceptions.png>)

### Exceptions by Vendor
![Exceptions by Vendor](<Exceptions by Vendor.png>)

## Business Context
In contractor order fulfillment, order entry defects (duplicate POs, missing jobsite postal codes, negative quantities, overdue shipments) frequently bypass standard POS checks. This project automates multi-vendor exception auditing and generates formatted Excel workbooks to speed fulfillment resolution.

## Operational Rules & Severity
* **CRITICAL — Duplicate Order IDs:** Evaluated across all source records to detect PO conflicts.
* **CRITICAL — Overdue Open Orders:** Open shipments where expected delivery is prior to the benchmark date (**2026-10-31**).
* **HIGH — Missing Destination Postal Codes:** Active shipments lacking postal routing parameters.
* **MEDIUM — Non-Positive Quantities:** Zero or negative line-item quantities on active orders.

*Exclusion Rule:* Cancelled and Inactive orders are excluded from delivery-aging, missing-zip, and quantity audits to prevent false-positive alerts.

---

## Quickstart

```bash
git clone https://github.com/elliot-sandburg/order-exception-tracker.git
cd order-exception-tracker
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
python validator.py
```

---

## Relational Database Extension (`/sql`)

To simulate enterprise ERP environments, this project includes a normalized SQLite database architecture and SQL query library:
* **`schema.sql`**: Third Normal Form (3NF) schema with primary/foreign keys, B-tree indexes, and a SQL reporting view (`v_vendor_performance_summary`).
* **`ingest_to_db.py`**: Automated Python ETL script that normalizes `orders_raw.csv`, quarantines colliding duplicate Order IDs to `quarantined_duplicates.csv` to prevent vendor misattribution, and enforces transactional row-count reconciliation.
* **`queries.sql` & `run_queries.py`**: Analytical SQL audit suite tracking vendor overdue rates, recorded value of overdue open orders, and ledger discrepancies against the 2026-10-31 benchmark date.
* **`DESIGN.md`**: Architectural design document detailing the 3NF data model, indexing decisions, and operational assumptions.

### Database Execution:
```bash
python sql/ingest_to_db.py
python sql/run_queries.py
```