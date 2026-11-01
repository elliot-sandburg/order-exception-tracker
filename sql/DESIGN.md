# Architecture Document: Retail Operations & Vendor Exception Database

**Author:** Elliot Sandburg  
**Location:** Eugene, Oregon, United States  
**Project:** Independent Data Pipeline Portfolio Extension

## Scope
The Retail Operations & Vendor Exception Database provides a normalized relational backend to model commercial building material order lifecycles, contractor accounts, vendor reliability metrics, and operational exception detection.

### In Scope:
* Tracking supplier entities and lead times for primary flooring manufacturers (Mohawk, Shaw, Armstrong, Daltile).
* Capturing order header parameters (order dates, expected delivery dates, fulfillment status, commercial contractor accounts, destination postal routing).
* Item-level line allocations (quantities, wholesale valuations).
* Automated exception audits identifying overdue open shipments, missing routing zip codes, and non-positive inventory allocations.

### Out of Scope:
* Consumer credit card transaction processing (PCI-DSS compliance).
* Warehouse bin-aisle slotting and physical freight GPS tracking.

---

## Functional Requirements
The database allows operations coordinators and data analysts to:
1. Ingest multi-vendor order extracts into third normal form (3NF).
2. Execute automated exception queries identifying supply chain bottlenecks.
3. Quantify financial risk by calculating total recorded value tied up in overdue orders.
4. Calculate vendor-specific defect percentages to guide restock procurement negotiations.

---

## Representation (Entity-Relationship Model)

```text
[vendors] 1 ────< N [orders] 1 ────< N [order_items]
```

1. **`vendors`**: Represents external manufacturers and distributors (Mohawk, Shaw, Armstrong, Daltile).
2. **`orders`**: Represents purchase order headers (Order ID, Customer, Vendor, Dates, Zip, Status).
3. **`order_items`**: Represents line-item specifications linked to an order (Item ID, Order ID, Quantity, Unit Price).

---

## Optimizations
* **B-Tree Indexes**: Added indexes on `orders(status, expected_delivery)` and `order_items(order_id)` to support rapid status filtering and join execution.
* **SQL Reporting View**: `v_vendor_performance_summary` aggregates order volumes, distinct overdue order counts, and pipeline valuation into a single queryable table.

---

## Assumptions & Limitations
* **One Row Per Order Assumption:** The source demonstration assumes each row represents a distinct order. Colliding duplicate IDs represent unresolved data-entry conflicts.
* **Single-Leg Deliveries:** Assumes orders are fulfilled in a single freight drop; does not currently track split shipments across multiple dates.