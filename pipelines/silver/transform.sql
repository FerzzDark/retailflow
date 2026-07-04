-- Silver layer: clean, normalize, and enrich sales data.
-- Unpivots the wide day-columns format into a long daily grain,
-- joins with calendar and prices, and adds calendar features.

CREATE OR REPLACE TABLE `retailflow.silver.silver_sales_daily` AS
WITH unpivoted AS (
  -- Convert wide format (d_1, d_2, ...) into long format (day, units)
  SELECT
    id,
    item_id,
    cat_id,
    store_id,
    state_id,
    day_col AS d,
    units
  FROM `retailflow.bronze.bronze_sales`
  UNPIVOT(units FOR day_col IN (d_1, d_2 /* ... expand for full range ... */))
),
enriched AS (
  SELECT
    u.id,
    u.item_id,
    u.cat_id,
    u.store_id,
    u.state_id,
    c.date,
    u.units,
    c.wday,
    c.month,
    c.year,
    c.event_name_1,
    c.event_type_1,
    -- SNAP flag depends on state
    CASE u.state_id
      WHEN 'CA' THEN c.snap_CA
      WHEN 'TX' THEN c.snap_TX
      WHEN 'WI' THEN c.snap_WI
    END AS snap_flag,
    p.sell_price
  FROM unpivoted u
  LEFT JOIN `retailflow.bronze.bronze_calendar` c ON u.d = c.d
  LEFT JOIN `retailflow.bronze.bronze_prices` p
    ON u.store_id = p.store_id
   AND u.item_id = p.item_id
   AND c.wm_yr_wk = p.wm_yr_wk
)
SELECT
  *,
  -- Feature: is this a weekend?
  CASE WHEN wday IN (1, 2) THEN 1 ELSE 0 END AS is_weekend,
  -- Feature: does the item have a price (was it on sale)?
  CASE WHEN sell_price IS NOT NULL THEN 1 ELSE 0 END AS is_active
FROM enriched;
