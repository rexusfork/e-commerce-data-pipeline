
-- 1. Total sales revenue (GBP)
SELECT
    SUM(total_amount) AS gross_sales_revenue
FROM sales;

-- 2. Top 10 products by revenue
SELECT
    stock_code,
    MAX(description) AS product_description,
    SUM(quantity) AS total_quantity,
    SUM(total_amount) AS total_revenue
FROM sales
GROUP BY stock_code
ORDER BY total_revenue DESC
LIMIT 10;

-- 3. Monthly sales trend
SELECT
    DATE_TRUNC('month', invoice_date)::DATE AS month,
    COUNT(DISTINCT invoice_no) AS total_orders,
    SUM(total_amount) AS gross_sales_revenue
FROM sales
GROUP BY 1
ORDER BY 1;

-- 4. Revenue by country
SELECT
    country,
    SUM(total_amount) AS total_revenue
FROM sales
GROUP BY country
ORDER BY total_revenue DESC;

-- 5. Cancellation summary
SELECT
    COUNT(*) AS cancelled_lines,
    ABS(SUM(total_amount)) AS cancellation_value
FROM cancellations;

-- 6. Data quality summary
SELECT
    rejection_reason,
    COUNT(*) AS rejected_count
FROM rejected
GROUP BY rejection_reason
ORDER BY rejected_count DESC;


-- Latest pipeline executions
SELECT
    run_id,
    status,
    started_at,
    finished_at,
    ROUND(duration_seconds::NUMERIC, 2) AS duration_seconds
FROM pipeline_runs
ORDER BY started_at DESC
LIMIT 20;

-- Average duration of successful executions
SELECT
    COUNT(*) AS successful_runs,
    ROUND(
        AVG(duration_seconds)::NUMERIC, 2
    ) AS avg_duration_seconds
FROM pipeline_runs
WHERE status = 'SUCCESS';

-- Failed execution history
SELECT
    run_id,
    started_at,
    error_message
FROM pipeline_runs
WHERE status = 'FAILED'
ORDER BY started_at DESC;

-- Extraction and transformation timings
SELECT
    run_id,
    (metrics->>'extract_seconds')::NUMERIC AS extract_seconds,
    (metrics->>'transform_seconds')::NUMERIC AS transform_seconds,
    (metrics->>'load_seconds')::NUMERIC AS load_seconds
FROM pipeline_runs
WHERE status = 'SUCCESS'
ORDER BY run_id DESC;
