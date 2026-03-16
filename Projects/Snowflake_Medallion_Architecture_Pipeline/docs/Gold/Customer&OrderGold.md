# Customer & Order Gold Layer Documentation

## 1. Overview
The Gold Layer provides curated, analytics-ready views designed specifically for BI dashboards and reporting. It builds on cleaned, standardised Silver data and transforms it into aggregated, business-aligned metrics for customer behaviour, order performance, operational insights, and commercial KPIs.

This document follows the same structure and style as the existing Bronze and Silver documentation, providing:
- High-level purpose
- Core principles
- Summary of business logic
- View-by-view documentation (purpose, inputs, outputs, and logic)
- References to underlying SQL files stored in the repository

It is intended for analysts, engineers, and anyone maintaining or extending reporting logic.

---
## 2. Gold Layer Principles
The following principles apply to Customer & Order Gold outputs and should be considered non-negotiable unless explicitly versioned in a change log.

### 2.1 Customer Identity & Deduplication
- A single real-world person can hold multiple `customer_id`s (e.g., duplicate accounts).
- For **first-order** attribution, each `customer_id` is counted as a new customer at the time of its first order.
- To avoid downstream over-counting in person-level analyses, grouping logic consolidates records that share the same name + date of birth when required.

### 2.2 Order Validity
- Only orders with `state = 'delivered'` are included in all sales and order‑volume metrics.
- Orders in any cancelled or non-delivered state are excluded from Gold aggregates.

### 2.3 Calendar Spine & Zero‑Fill
- The Gold layer constructs a **complete date spine** so that every date is represented in time‑series outputs.
- Dates with no activity are **zero‑filled** (e.g., `0` orders, `0` sales) to ensure continuous charts and consistent averages.

### 2.4 Year‑to‑Date (YTD) Calculations
- YTD averages include **all** days in the period, including zero‑order days, to reflect true operational performance rather than “active‑days only”.

### 2.5 Order Timing Interpretation
- If an order is placed on one date and delivered on another, this is **not considered scheduled/planned** behaviour; it reflects operational timing only.

### 2.6 Order Attribution
- All Gold metrics attribute activity to the **order creation timestamp** (`order_time`), *not* pickup or delivery timestamps.

### 2.7 Order Total Calculation
- `order_total` is already **net of discounts** in the source.
- No additional discounting is applied at Gold; sales metrics always use the post‑discount value.

### 2.8 Null Handling Rules
- When aggregating numeric fields, `NULL` is treated as `0` to stabilise calculations (e.g., ratios, percentage change, YTD).
- This reflects the assumption that a missing value indicates **no activity**, not an error state.

---
## 3. Gold Views
Below are the documented Gold views derived from the SQL definitions located in the repository. Each section includes:
- Purpose
- Derived from (input tables)
- Logic summary
- Output (key fields)
- Example SQL snippet
- Link to source SQL
- **Gold principle integration** (how global rules apply to this view)

---
### 3.1 TOTAL_ORDERS
**Purpose**  
Provides daily delivered order counts with calendar spine expansion for complete BI time‑series reporting.

**Derived From**  
- `SILVER_ORDERS`

**Key Logic**
- Filter to `state = 'delivered'`.
- Group by `DATE(order_time)`.
- Left‑join to full calendar spine and zero‑fill missing days.

**Output (key columns)**
- `order_date`
- `total_orders`

**Gold principle integration**
- **Order Validity:** delivered‑only.  
- **Calendar Spine & Zero‑Fill:** ensures continuous daily series.  
- **Attribution:** uses `order_time` date.  
- **Null Handling:** gaps resolved by zero‑fill (no NULL counts).  
- **YTD:** averages include zero‑order days.

**Example Snippet**
```sql
SELECT DATE(order_time) AS order_date, COUNT(*) AS total_orders
FROM silver_orders
WHERE state = 'delivered'
GROUP BY 1;
```

---
### 3.2 TOTAL_SALES
**Purpose**  
Calculates daily net sales across delivered orders using already‑discounted `order_total` values.

**Derived From**  
- `SILVER_ORDERS`

**Key Logic**
- Filter to `state = 'delivered'`.
- Sum `order_total` by `DATE(order_time)`.
- Join to calendar spine for full continuity.

**Output (key columns)**
- `order_date`
- `total_sales`

**Gold principle integration**
- **Order Total Calculation:** uses post‑discount `order_total` as‑is.  
- **Order Validity:** delivered‑only.  
- **Attribution:** `order_time` date.  
- **Calendar Spine & Zero‑Fill:** complete daily coverage.  
- **Null Handling:** non‑existent days present as `0` sales.

**Example Snippet**
```sql
SELECT DATE(order_time) AS order_date, SUM(order_total) AS total_sales
FROM silver_orders
WHERE state = 'delivered'
GROUP BY 1;
```


---
### 3.3 NEW_CUSTOMERS
**Purpose**  
Identifies the first‑ever purchasers and computes daily new customer counts.

**Derived From**  
- `SILVER_CUSTOMER`
- `SILVER_ORDERS`

**Key Logic**
- Determine earliest order date per `customer_id`.
- Count customers whose first order occurs on each date.
- When required by downstream analysis, consolidate multiple `customer_id`s belonging to the same person (name + DOB).

**Output (key columns)**
- `first_order_date`
- `new_customers`

**Gold principle integration**
- **Customer Identity & Deduplication:** governs consolidation rules beyond raw `customer_id`.  
- **Attribution:** first order uses `order_time`.  
- **YTD:** averages/counts may include days with `0` new customers.  
- **Null Handling:** customers without any order have `NULL` first order dates and are excluded from counts.

**Example Snippet**
```sql
SELECT first_order_date, COUNT(*) AS new_customers
FROM silver_customer
WHERE first_order_date IS NOT NULL
GROUP BY 1;
```

---
### 3.4 AVERAGE_PICK_UP_TIME
**Purpose**  
Calculates mean pickup duration (minutes) across delivered orders.

**Derived From**  
- `SILVER_ORDERS`

**Key Logic**
- Compute `pickup_time - order_time` in minutes.
- Average by day of `order_time`.
- Restrict to delivered orders.

**Output (key columns)**
- `order_date`
- `avg_pickup_minutes`

**Gold principle integration**
- **Order Validity:** delivered‑only.  
- **Attribution:** attributed to `order_time` date (not pickup time).  
- **YTD / Null Handling:** zero‑activity days appear with `NULL` average unless explicitly zero‑filled in reporting; counts use zero‑fill where appropriate.

**Example Snippet**
```sql
SELECT DATE(order_time) AS order_date,
       AVG(DATEDIFF('minute', order_time, pickup_time)) AS avg_pickup_minutes
FROM silver_orders
WHERE state = 'delivered'
GROUP BY 1;
```


---
### 3.5 AVERAGE_DELIVERY_TIME
**Purpose**  
Computes the average time (minutes) between pickup and delivery.

**Derived From**  
- `SILVER_ORDERS`

**Key Logic**
- Calculate `delivery_time - pickup_time` in minutes.
- Average by day of `order_time`.
- Restrict to delivered orders.

**Output (key columns)**
- `order_date`
- `avg_delivery_minutes`

**Gold principle integration**
- **Order Validity:** delivered‑only.  
- **Attribution:** attributed to `order_time` date (not delivery time).  
- **YTD / Null Handling:** behaviour mirrors pickup metric; ensure zero‑fill strategy aligns with dashboard expectation.

**Example Snippet**
```sql
SELECT DATE(order_time) AS order_date,
       AVG(DATEDIFF('minute', pickup_time, delivery_time)) AS avg_delivery_minutes
FROM silver_orders
WHERE state = 'delivered'
GROUP BY 1;
```



---
## 4. End-to-End Data Flow (Text Diagram)
```
BRONZE → SILVER → GOLD
(Customer & Order BI Metrics)
```

---
## 5. Summary
The Customer & Order Gold layer provides a clean, curated, analytics-ready set of KPIs built on top of validated Silver datasets. It standardises business logic, ensures consistent metric definitions, and supports reliable dashboarding.

All SQL is maintained in the repository and should be updated alongside any changes to this documentation.

---
