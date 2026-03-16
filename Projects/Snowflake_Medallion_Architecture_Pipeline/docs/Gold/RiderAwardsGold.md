# Rider Awards Gold Layer Documentation

## 1. Overview
The Rider Awards Gold Layer provides curated, analytics-ready award and activity views for dashboards relating to rider performance. These views are derived from clean Silver data and summarise rider behaviour, deliveries, tenure, distance, and award classifications over defined rolling windows.

This documentation aligns with the same structure used for the Bronze, Silver, and Customer Gold layers. It provides:
- High-level concepts and business definitions
- Gold-layer rider principles
- Detailed explanations of each award and activity view
- Example SQL snippets (not full code)
- Clear handover guidance for analysts and engineers

---
## 2. Rider Gold Layer Principles
These principles are taken directly from the provided rider documentation and apply to all rider Gold-layer outputs.

### 2.1 Active Rider Definition
An **Active Rider** is any rider who has completed **at least 1 delivery in the last 28 days**.

### 2.2 Power Rider Definition
A **Power Rider** is any rider who has completed **at least 7 deliveries in the last 7 days**.

### 2.3 Last Year Definition
“**Last year**” refers to a **rolling 365‑day window** measured backwards from the current date.

### 2.4 Award Definitions & Justifications
Each award has specific business logic and justification.

#### Most Deliveries Award
- Awarded to the **top three riders (with ties)** who completed the most deliveries in the last year.
- *Delivered* and *cancelled* orders both count (so riders are not penalised for issues outside their control).

#### Most Travelled Award
- Awarded to riders with the **highest total travel distance** over the last year.
- Distance is calculated **as the crow flies**, from restaurant to delivery location.

#### Big Day Award
- Awarded to the **top three riders (with ties)** who completed the most deliveries in a **single day** within the last year.
- Ties are broken using **total distance travelled** that day.

#### Longest Serving Award
- Awarded to the **top three active riders (with ties)** who have the **earliest join date**.
- Ties are broken using **total deliveries completed**.

---
## 3. Gold Views
Below are the Gold views created for rider dashboards. For each view we document:
- Purpose
- Inputs (Silver tables)
- Business logic summary
- Gold‑principle integration
- Output fields
- Example SQL snippet

---
### 3.1 ACTIVE_RIDERS
**Purpose:** Identify riders active in the last 28 days.

**Derived From:** `SILVER_ORDERS`

**Logic Summary:**
- Select distinct `rider_id` where `delivery_time` ≥ current_date - 28 days.

**Output:**
- `rider_id`

**Example Snippet:**
```sql
SELECT DISTINCT rider_id
FROM silver_orders
WHERE delivery_time >= DATEADD(day, -28, CURRENT_DATE);
```

---
### 3.2 ACTIVE_RIDERS_PREV_MONTH
**Purpose:** Identify riders active in the *previous* 28‑day window.

**Window:** -56 to -28 days.

**Example Snippet:**
```sql
SELECT DISTINCT rider_id
FROM silver_orders
WHERE delivery_time >= DATEADD(day, -56, CURRENT_DATE)
  AND delivery_time < DATEADD(day, -28, CURRENT_DATE);
```

---
### 3.3 POWER_RIDERS
**Purpose:** Identify riders completing 7+ deliveries in the last 7 days.

**Logic Summary:** Group by `rider_id` over 7‑day window; keep counts ≥ 7.

**Output:** rider_id

**Example Snippet:**
```sql
SELECT rider_id
FROM silver_orders
WHERE delivery_time >= DATEADD(day, -7, CURRENT_DATE)
GROUP BY rider_id
HAVING COUNT(order_id) >= 7;
```

---
### 3.4 POWER_RIDERS_PREV_WEEK
Same logic as POWER_RIDERS but for previous 7‑day window.

---
### 3.5 NEW_RIDERS
**Purpose:** Identify riders who joined within the last 7 days.

**Derived From:** `SILVER_RIDER`

**Output:** rider_id, full_name, join_date

**Example:**
```sql
SELECT rider_id, TRIM(CONCAT(first_name, ' ', last_name)) AS full_name, join_date
FROM silver_rider
WHERE join_date >= DATEADD(day, -7, CURRENT_DATE);
```

---
### 3.6 NEW_RIDERS_PREV_WEEK
Same structure but window is -14 to -7 days.

---
## 4. Award Views
These Gold views power the Rider Awards dashboard.

---
### 4.1 MOST_DELIVERIES_AWARD
**Purpose:** Top 3 riders (with ties) by delivery count in the last 365 days.

**Inputs:** `SILVER_ORDERS`, `SILVER_RIDER`

**Logic Summary:**
- Count deliveries per rider over last year.
- Apply `DENSE_RANK()` ordering by delivery_count DESC.
- QUALIFY rank <= 3.
- Both delivered + cancelled orders count.

**Outputs:** rider_id, full_name, delivery_count, rank

**Example:**
```sql
SELECT rider_id,
       full_name,
       COUNT(order_id) AS delivery_count,
       DENSE_RANK() OVER (ORDER BY COUNT(order_id) DESC) AS rank
FROM silver_orders o
JOIN silver_rider r USING (rider_id)
WHERE delivery_time >= DATEADD(day, -365, CURRENT_DATE)
GROUP BY rider_id, full_name
QUALIFY rank <= 3;
```

---
### 4.2 MOST_TRAVELLED_AWARD
**Purpose:** Award rider who travelled the most miles in the last 365 days.

**Logic Summary:**
- Compute distance for each delivery using HAVERSINE.
- Sum total miles per rider.
- Rank by total miles.

**Outputs:** rider_id, full_name, total_miles_travelled, rank

---
### 4.3 BIG_DAY_AWARD
**Purpose:** Top 3 riders with the most deliveries on a **single day**.

**Logic Summary:**
- Count deliveries per rider per date.
- Compute total miles for that date.
- Rank by deliveries DESC, then miles DESC.

**Outputs:** rider_id, date, delivery_count, total_miles_travelled, rank

---
### 4.4 LONGEST_SERVING_AWARD
**Purpose:** Top 3 active riders with earliest join date.

**Logic Summary:**
- Filter to active riders (last 28 days).
- Rank by join date ASC, tie‑break using total deliveries.

**Example:**
```sql
WITH active AS (
    SELECT DISTINCT rider_id
    FROM silver_orders
    WHERE delivery_time >= DATEADD(day, -28, CURRENT_DATE)
), stats AS (
    SELECT r.rider_id, r.full_name, r.join_date,
           COUNT(o.order_id) AS total_deliveries
    FROM silver_rider r
    JOIN active a USING (rider_id)
    LEFT JOIN silver_orders o USING (rider_id)
    GROUP BY 1,2,3
)
SELECT *, DENSE_RANK() OVER (ORDER BY join_date ASC, total_deliveries DESC) AS rank
FROM stats
QUALIFY rank <= 3;
```

---
## 5. End-to-End Flow
```
BRONZE  →  SILVER (rider, orders, restaurant)
        →  GOLD (activity + awards)
```

---
## 6. Summary
The Rider Awards Gold Layer provides all core award and activity metrics required for dashboarding, planning, and performance reporting. These views formalise business definitions, handle ties consistently, and ensure that both distance and delivery‑based metrics are calculated in a transparent, repeatable manner.

All SQL is maintained in the repository and should be updated in tandem with this documentation.
