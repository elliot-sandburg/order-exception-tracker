-- ============================================================
-- AUDIT QUERY 1: Vendor Late-Fulfillment Rate Summary
-- Benchmark Date: 2026-10-31
-- ============================================================
SELECT 
    v.vendor_name,
    COUNT(o.order_id) AS total_orders,
    COUNT(DISTINCT CASE WHEN o.expected_delivery < '2026-10-31' AND o.status = 'Open' THEN o.order_id END) AS overdue_orders,
    ROUND(
        CAST(COUNT(DISTINCT CASE WHEN o.expected_delivery < '2026-10-31' AND o.status = 'Open' THEN o.order_id END) AS FLOAT) 
        / COUNT(o.order_id) * 100, 2
    ) AS overdue_rate_pct
FROM vendors v
JOIN orders o ON v.vendor_id = o.vendor_id
GROUP BY v.vendor_id, v.vendor_name
ORDER BY overdue_rate_pct DESC;

-- ============================================================
-- AUDIT QUERY 2: Value of Overdue Open Orders
-- Benchmark Date: 2026-10-31
-- ============================================================
SELECT 
    v.vendor_name,
    COUNT(DISTINCT o.order_id) AS stalled_orders,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS overdue_order_value_usd
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN vendors v ON o.vendor_id = v.vendor_id
WHERE o.status = 'Open' 
  AND o.expected_delivery < '2026-10-31'
GROUP BY v.vendor_name
ORDER BY overdue_order_value_usd DESC;

-- ============================================================
-- AUDIT QUERY 3: Missing Destination Postal Code Audit
-- Status-aware: Checks active fulfillment orders (Open/Pending)
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
-- AUDIT QUERY 4: Non-Positive Line Item Quantity Audit
-- Status-aware: Excludes Cancelled/Inactive orders (Matches Python logic)
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
WHERE oi.quantity <= 0
  AND o.status NOT IN ('Cancelled', 'Inactive');

-- ============================================================
-- AUDIT QUERY 5: Reporting View Execution
-- Reads directly from v_vendor_performance_summary
-- ============================================================
SELECT * 
FROM v_vendor_performance_summary 
WHERE total_delayed_orders > 0
ORDER BY total_delayed_orders DESC;