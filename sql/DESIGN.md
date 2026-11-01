# Design Document: Retail Operations & Vendor Exception Database

**Author:** Elliot Sandburg
**Location:** Eugene, Oregon, United States
**Course:** CS50's Introduction to Databases with SQL (CS50 SQL Capstone Project)

## Scope

The Retail Operations & Vendor Exception Database provides a normalized relational backend to model commercial building material order lifecycles, contractor accounts, vendor reliability metrics, and operational exception detection.

### In Scope:
* Tracking supplier entities and lead-time contracts for primary flooring manufacturers (Mohawk Industries, Shaw Floors, Armstrong Flooring, Daltile).
* Capturing order header parameters (order dates, expected delivery dates, fulfillment status, commercial contractor accounts, destination postal routing).
* Item-level line allocations (quantities, wholesale valuations).
* Exception audits identifying overdue shipments, missing routing zip codes, and negative inventory allocations.

### Out of Scope:
* Consumer credit card transaction processing (PCI-DSS compliance).
* Warehouse bin-aisle slotting and physical freight GPS tracking.
* Retail customer CRM rewards programs.

---

## Functional Requirements

The database allows operations coordinators and data analysts to:
1. Ingest multi-vendor order extracts into third normal form (3NF).
2. Execute automated exception queries identifying supply chain bottlenecks.
3. Quantify financial risk by calculating total capital stalled in transit.
4. Calculate vendor-specific defect percentages to guide restock procurement negotiations.

---

## Representation

### Entities & Relationships (Entity-Relationship Model)

```text
[vendors] 1 ────< N [orders] 1 ────< N [order_items]