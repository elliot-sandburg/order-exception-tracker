# Retail Order-Exception & Fulfillment Validation Pipeline

An automated data-integrity and fulfillment validation engine built in Python (`pandas`, `openpyxl`). Ingests multi-vendor order extracts, audits operational parameters against core business rules, excludes inactive/cancelled records to prevent false positives, and generates an itemized discrepancy workbook with vendor performance scorecards.

## Business Context
In contractor order fulfillment and building materials distribution, order entry defects (duplicate POs, missing jobsite postal codes, negative quantities, overdue shipments) frequently bypass standard POS checks. These issues cause delivery delays, site downtime, and vendor disputes.

This pipeline automates pre-dispatch auditing to identify fulfillment exceptions before orders reach the supplier dispatch stage.

## Operational Rules & Severity
Each row represents a discrete Vendor Purchase Order (PO):
- **CRITICAL:** Duplicate Order IDs (checked across all records to catch double-billing).
- **CRITICAL:** Overdue Open Fulfillment (active orders where expected delivery is past the current run date).
- **HIGH:** Missing destination postal codes on active shipments.
- **MEDIUM:** Non-Positive line-item quantities on active shipments.

*Exclusion Rule:* Cancelled and Inactive orders are automatically filtered prior to evaluating quantity and delivery aging rules to eliminate false positives.

## Benchmark Execution Results
Tested on a synthetic benchmark dataset of **520 multi-vendor order records**:
- **Total Records Ingested:** 520
- **Total Operational Exception Events:** 33 events across 26 unique affected orders
  - *Critical (Duplicate IDs):* 6
  - *Critical (Overdue Open Orders):* 15
  - *High (Missing Postal Codes):* 7
  - *Medium (Invalid Quantities):* 5

### Vendor Performance Scorecard
| Vendor Name | CRITICAL | HIGH | MEDIUM | TOTAL_EXCEPTIONS |
| :--- | :---: | :---: | :---: | :---: |
| **Mohawk Industries** | 7 | 2 | 2 | **11** |
| **Shaw Floors** | 6 | 2 | 1 | **9** |
| **Armstrong Flooring** | 5 | 2 | 1 | **8** |
| **Daltile** | 3 | 1 | 1 | **5** |

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
python generate_data.py
python validator.py
```

## Relational Database Extension (`/sql`)

To simulate enterprise ERP environments, this project includes a normalized SQLite database architecture and SQL query library:
* **`schema.sql`**: Third Normal Form (3NF) schema with primary/foreign keys, B-tree indexes, and an executive reporting view (`v_vendor_performance_summary`).
* **`ingest_to_db.py`**: Automated Python ETL script normalizing `orders_raw.csv` into relational tables with foreign key validation.
* **`queries.sql` & `run_queries.py`**: Analytical SQL audit suite calculating supplier defect rates, stalled transit capital, missing shipping zips, and ledger discrepancies.
* **`DESIGN.md`**: Comprehensive architectural design thesis prepared for the Harvard University CS50 SQL Capstone.