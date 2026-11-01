-- ============================================================
-- RETAIL OPERATIONS & EXCEPTION AUDITING DATABASE
-- Harvard CS50 SQL Capstone Project / Tier 2 Data Pipeline
-- ============================================================

PRAGMA foreign_keys = ON;

DROP VIEW IF EXISTS v_vendor_performance_summary;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS vendors;

-- 1. VENDORS TABLE
CREATE TABLE vendors (
    vendor_id TEXT PRIMARY KEY,
    vendor_name TEXT NOT NULL UNIQUE,
    lead_time_days INTEGER NOT NULL DEFAULT 7,
    status TEXT NOT NULL DEFAULT 'Active'
);

-- 2. PURCHASE ORDERS (Header Table)
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    vendor_id TEXT NOT NULL,
    order_date DATE NOT NULL,
    expected_delivery DATE NOT NULL,
    shipping_zip TEXT,
    status TEXT NOT NULL,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE RESTRICT
);

-- 3. ORDER LINE ITEMS (Detail Table)
CREATE TABLE order_items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

-- ============================================================
-- PERFORMANCE OPTIMIZATIONS: B-TREE INDEXES
-- ============================================================

CREATE INDEX idx_orders_status_delivery 
ON orders (status, expected_delivery);

CREATE INDEX idx_order_items_order_id 
ON order_items (order_id);

CREATE INDEX idx_orders_vendor_id 
ON orders (vendor_id);

-- ============================================================
-- REPORTING OPTIMIZATION: MATERIALIZED LOGICAL VIEW
-- ============================================================

CREATE VIEW v_vendor_performance_summary AS
SELECT 
    v.vendor_id,
    v.vendor_name,
    COUNT(DISTINCT o.order_id) AS total_orders_placed,
    SUM(CASE WHEN o.expected_delivery < DATE('now') AND o.status = 'Open' THEN 1 ELSE 0 END) AS total_delayed_orders,
    ROUND(
        CAST(SUM(CASE WHEN o.expected_delivery < DATE('now') AND o.status = 'Open' THEN 1 ELSE 0 END) AS FLOAT) 
        / NULLIF(COUNT(DISTINCT o.order_id), 0) * 100, 2
    ) AS overdue_rate_pct,
    COALESCE(ROUND(SUM(oi.quantity * oi.unit_price), 2), 0) AS total_pipeline_value_usd
FROM vendors v
LEFT JOIN orders o ON v.vendor_id = o.vendor_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY v.vendor_id, v.vendor_name;