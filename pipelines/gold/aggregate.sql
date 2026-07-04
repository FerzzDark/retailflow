-- Gold layer: business-ready aggregations and star schema.

-- Fact table: daily sales at product-store grain
CREATE OR REPLACE TABLE `retailflow.gold.fact_sales` AS
SELECT
  id,
  item_id,
  store_id,
  date,
  units,
  sell_price,
  units * IFNULL(sell_price, 0) AS revenue
FROM `retailflow.silver.silver_sales_daily`;

-- Dimension: product
CREATE OR REPLACE TABLE `retailflow.gold.dim_product` AS
SELECT DISTINCT item_id, cat_id
FROM `retailflow.silver.silver_sales_daily`;

-- Dimension: store
CREATE OR REPLACE TABLE `retailflow.gold.dim_store` AS
SELECT DISTINCT store_id, state_id
FROM `retailflow.silver.silver_sales_daily`;

-- Business view: weekly sales by category (for dashboard)
CREATE OR REPLACE VIEW `retailflow.gold.weekly_category_sales` AS
SELECT
  cat_id,
  store_id,
  DATE_TRUNC(date, WEEK) AS week,
  SUM(units) AS total_units,
  SUM(units * IFNULL(sell_price, 0)) AS total_revenue,
  AVG(units) AS avg_daily_units
FROM `retailflow.silver.silver_sales_daily`
GROUP BY cat_id, store_id, week;

-- Supply chain KPI view: ABC classification by revenue
CREATE OR REPLACE VIEW `retailflow.gold.abc_classification` AS
WITH product_revenue AS (
  SELECT
    item_id,
    SUM(units * IFNULL(sell_price, 0)) AS total_revenue
  FROM `retailflow.silver.silver_sales_daily`
  GROUP BY item_id
),
ranked AS (
  SELECT
    item_id,
    total_revenue,
    PERCENT_RANK() OVER (ORDER BY total_revenue DESC) AS pct_rank
  FROM product_revenue
)
SELECT
  item_id,
  total_revenue,
  CASE
    WHEN pct_rank <= 0.2 THEN 'A'
    WHEN pct_rank <= 0.5 THEN 'B'
    ELSE 'C'
  END AS abc_class
FROM ranked;
