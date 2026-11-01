-- ============================================================
-- AUDIT QUERY 1: Vendor Fulfillment Defect Rate (Scorecard)
-- Calculates overdue rate across all 4 primary vendors
-- ============================================================
SELECT
    v.vendor_name,
    COUNT(o.order_id) AS total_orders,
    SUM(CASE WHEN o.expected_delivery < DATE('now') AND o.status = 'Open' THEN 1 ELSE 0 END) AS overdue_orders,
    ROUND(
        CAST(SUM(CASE WHEN o.expected_delivery < DATE('now') AND o.status = 'Open' THEN 1 ELSE 0 END) AS FLOAT)
        / COUNT(o.order_id) * 100, 2
    ) AS defect_rate_pct
FROM vendors v
JOIN orders o ON v.vendor_id = o.vendor_id
GROUP BY v.vendor_id, v.vendor_name
ORDER BY defect_rate_pct DESC;

-- ============================================================
-- AUDIT QUERY 2: Financial Capital at Risk (Delayed Freight)
-- Quantifies the exact dollar amount stalled in transit
-- ============================================================
SELECT
    v.vendor_name,
    COUNT(DISTINCT o.order_id) AS stalled_orders,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS tied_up_capital_usd
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN vendors v ON o.vendor_id = v.vendor_id
WHERE o.status = 'Open'
  AND o.expected_delivery < DATE('now')
GROUP BY v.vendor_name
ORDER BY tied_up_capital_usd DESC;

-- ============================================================
-- AUDIT QUERY 3: Missing Shipping Manifest Anomaly (Fraud/Customs Audit)
-- Flags active orders released for delivery lacking postal routing parameters
-- ============================================================
SELECT
    o.order_id,
    o.customer_name,
    v.vendor_name,
    o.order_date,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS order_total_usd
FROM orders o
JOIN vendors v ON o.vendor_id = v.vendor_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE (o.shipping_zip IS NULL OR TRIM(o.shipping_zip) = '')
  AND o.status IN ('Open', 'Pending')
GROUP BY o.order_id, o.customer_name, v.vendor_name, o.order_date
ORDER BY order_total_usd DESC;

-- ============================================================
-- AUDIT QUERY 4: Inventory Ledger Corruption Check (Negative Quantities)
-- Isolates data-entry errors before they corrupt ERP stock balances
-- ============================================================
SELECT
    oi.item_id,
    oi.order_id,
    o.customer_name,
    oi.quantity,
    oi.unit_price,
    v.vendor_name
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN vendors v ON o.vendor_id = v.vendor_id
WHERE oi.quantity <= 0;

-- ============================================================
-- AUDIT QUERY 5: Executive Performance View Execution
-- Reads directly from the pre-optimized virtual reporting view
-- ============================================================
SELECT *
FROM v_vendor_performance_summary
WHERE total_delayed_orders > 0
ORDER BY total_delayed_orders DESC;