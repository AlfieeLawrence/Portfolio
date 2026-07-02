
# Forecasting Documentation

This document describes the forecasting data preparation pipeline and output artifacts.

---
## 1) Purpose
Prepare an **analytics-ready fact table** with temporal and contextual features for **sales forecasting**.

---
## 2) Inputs (Silver Layer)
- `SILVER_ORDERS`
- `SILVER_CUSTOMER`
- `SILVER_RESTAURANT`

These are joined to assemble a unified training/inference dataset.

---
## 3) Processing Steps
### 3.1 Session & Context
- Use an active Snowflake / Snowpark session within your target Snowflake schema, for example `<SNOWFLAKE_DATABASE>.<SNOWFLAKE_SCHEMA>`.

### 3.2 Base Extract
- Select key columns from each Silver table:
  - Orders: `ORDER_ID, CUSTOMER_ID, RESTAURANT_ID, STATE, ORDER_TOTAL, ORDER_TIME`
  - Customer: `CUSTOMER_ID, MEMBERSHIP_TYPE`
  - Restaurant: `RESTAURANT_ID, RESTAURANT_NAME, FOOD_RATING, SERVICE_RATING, VALUE_RATING, AVG_PLATFORM_RATING, AVG_EXPERIENCE_RATING, BOROUGH`

### 3.3 Joins & Filters
- Left join Orders → Customer on `CUSTOMER_ID`
- Left join Orders → Restaurant on `RESTAURANT_ID`
- Filter: `STATE = 'delivered'` and `ORDER_TOTAL` / `ORDER_TIME` not null

### 3.4 Feature Engineering
- **Day of Week**: `dayofweek(ORDER_TIME)` (0=Sunday .. 6=Saturday)
- **Time of Day bucket** (via `hour(ORDER_TIME)`):
  - 04:00–07:59 → `Early Morning`
  - 08:00–11:59 → `Morning`
  - 12:00–15:59 → `Afternoon`
  - 16:00–19:59 → `Evening`
  - 20:00–23:59 → `Night`
  - 00:00–03:59 → `Late Night`
- **Season** (via `month(ORDER_TIME)`):
  - 12, 1, 2 → `Winter`
  - 3, 4, 5 → `Spring`
  - 6, 7, 8 → `Summer`
  - 9, 10, 11 → `Autumn`
- Retain contextual fields (ratings, membership, borough) for model signal.

### 3.5 Output Table
- Persist engineered dataset as **`SALESFORCASTDATA`** (overwrite mode) for modeling and BI.

---
## 4) Downstream Usage
- **Forecasting models** (e.g., time-series or supervised learners) consume `SALESFORCASTDATA`.
- **Dashboards** can aggregate by day/week/borough/restaurant and slice by `season`, `time_of_day`, `day_of_week`.

---
## 5) Reproducibility & Idempotency
- Transformations are deterministic; re-runs **overwrite** `SALESFORCASTDATA` to keep schema stable.
- Source-of-truth is the repo code; this doc is a human-readable summary of those steps.

---
## 6) Pseudocode (Snowpark)
```python
# set context
session.use_database('<SNOWFLAKE_DATABASE>')
session.use_schema('<SNOWFLAKE_SCHEMA>')

# load
orders = session.table('SILVER_ORDERS')
customers = session.table('SILVER_CUSTOMER')
restaurants = session.table('SILVER_RESTAURANT')

# join & filter
fact = (orders
        .join(customers, 'CUSTOMER_ID', 'left')
        .join(restaurants, 'RESTAURANT_ID', 'left')
        .filter((col('STATE')=='delivered') & col('ORDER_TIME').is_not_null() & col('ORDER_TOTAL').is_not_null()))

# features
fact = (fact
    .with_column('DAY_OF_WEEK', dayofweek(col('ORDER_TIME')))  # 0=Sun
    .with_column('SEASON', when(month('ORDER_TIME').isin(12,1,2),'Winter')
                          .when(month('ORDER_TIME').isin(3,4,5),'Spring')
                          .when(month('ORDER_TIME').isin(6,7,8),'Summer')
                          .otherwise('Autumn'))
    .with_column('TIME_OF_DAY',
        when((hour('ORDER_TIME')>=4) & (hour('ORDER_TIME')<8), 'Early Morning')
       .when((hour('ORDER_TIME')>=8) & (hour('ORDER_TIME')<12), 'Morning')
       .when((hour('ORDER_TIME')>=12) & (hour('ORDER_TIME')<16), 'Afternoon')
       .when((hour('ORDER_TIME')>=16) & (hour('ORDER_TIME')<20), 'Evening')
       .when((hour('ORDER_TIME')>=20) & (hour('ORDER_TIME')<=23), 'Night')
       .otherwise('Late Night')))

# save
fact.write.mode('overwrite').save_as_table('SALESFORCASTDATA')
```

---
## 7) Field Dictionary (Output)
| Column | Type | Notes |
|---|---|---|
| ORDER_ID | NUMBER | Unique order identifier |
| CUSTOMER_ID | NUMBER | From `SILVER_CUSTOMER` |
| RESTAURANT_ID | NUMBER | From `SILVER_RESTAURANT` |
| ORDER_TIME | TIMESTAMP | Event time |
| ORDER_TOTAL | NUMBER | Monetary total |
| STATE | VARCHAR | Filtered to `delivered` |
| DAY_OF_WEEK | NUMBER | 0..6 (Sun..Sat) |
| TIME_OF_DAY | VARCHAR | Categorical bucket |
| SEASON | VARCHAR | Winter/Spring/Summer/Autumn |
| MEMBERSHIP_TYPE | VARCHAR | Customer feature |
| FOOD_RATING / SERVICE_RATING / VALUE_RATING | FLOAT | Restaurant features |
| AVG_PLATFORM_RATING / AVG_EXPERIENCE_RATING | FLOAT | Platform/experience ratings |
| BOROUGH | VARCHAR | Location feature |

---
## 8) Notes
- Table name intentionally follows existing views/dashboards: **`SALESFORCASTDATA`**.
- Extendable: add holidays, promotions, weather, or lag features in future PRs.
