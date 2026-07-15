-- Core InsightIQ SQL checks used by the decision pipeline and the SQL Agent.

-- Revenue by month.
SELECT
    strftime('%Y-%m', order_date) AS month,
    COUNT(*) AS orders,
    SUM(CASE WHEN order_status = 'completed' THEN total_amount ELSE 0 END) AS completed_revenue,
    AVG(total_amount) AS average_order_value
FROM orders
GROUP BY 1
ORDER BY 1;

-- Funnel from product view to cart to purchase.
WITH event_counts AS (
    SELECT event_type, COUNT(DISTINCT user_id) AS users
    FROM events
    WHERE event_type IN ('view', 'cart')
    GROUP BY event_type
),
buyers AS (
    SELECT COUNT(DISTINCT user_id) AS users
    FROM orders
    WHERE order_status = 'completed'
)
SELECT 'view' AS step, users FROM event_counts WHERE event_type = 'view'
UNION ALL
SELECT 'cart' AS step, users FROM event_counts WHERE event_type = 'cart'
UNION ALL
SELECT 'purchase' AS step, users FROM buyers;

-- Category performance.
SELECT
    p.category,
    COUNT(DISTINCT oi.order_id) AS orders,
    SUM(oi.item_total) AS gross_item_revenue,
    AVG(r.rating) AS avg_review_rating,
    COUNT(DISTINCT r.review_id) AS review_count
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
LEFT JOIN reviews r ON r.product_id = p.product_id
GROUP BY p.category
ORDER BY gross_item_revenue DESC;

-- Products with high revenue but poor review quality.
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.item_total) AS revenue,
    AVG(r.rating) AS avg_review_rating,
    COUNT(DISTINCT r.review_id) AS reviews
FROM products p
JOIN order_items oi ON oi.product_id = p.product_id
LEFT JOIN reviews r ON r.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
HAVING reviews >= 5
ORDER BY revenue DESC, avg_review_rating ASC
LIMIT 25;
