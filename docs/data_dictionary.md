# Data Dictionary — M5 Forecasting Dataset

## sales_train_validation.csv
Daily unit sales per product per store (wide format).

| Column | Type | Description |
|--------|------|-------------|
| id | string | Unique series identifier |
| item_id | string | Product identifier |
| cat_id | string | Category (FOODS, HOBBIES, HOUSEHOLD) |
| store_id | string | Store identifier |
| state_id | string | State (CA, TX, WI) |
| d_1..d_1913 | int | Units sold each day |

## calendar.csv
| Column | Type | Description |
|--------|------|-------------|
| date | date | Calendar date |
| d | string | Day index |
| event_name_1 | string | Special events / holidays |
| snap_CA/TX/WI | int | SNAP assistance day flags |

## sell_prices.csv
| Column | Type | Description |
|--------|------|-------------|
| store_id | string | Store identifier |
| item_id | string | Product identifier |
| wm_yr_wk | int | Week identifier |
| sell_price | float | Price that week |
