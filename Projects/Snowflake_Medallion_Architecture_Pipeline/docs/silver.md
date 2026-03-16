
# Silver Layer Documentation

## 1. Overview
The Silver Layer converts raw Bronze data into clean, enriched, analytics‑ready datasets. These transformations support:

- Dashboard reporting
- Machine learning pipelines
- Gold layer computations
- Data Quality monitoring

Four curated Silver tables serve as the foundation:

1. `SILVER_CUSTOMER`
2. `SILVER_RIDER`
3. `SILVER_RESTAURANT`
4. `SILVER_ORDERS`

The clean‑and‑tidy pipeline runs after the main silver stage, to allow the data quality scripts to be run.

---
## 2. Silver Layer Principles
### 2.1 Data Cleaning
- Standardize data types
- Normalize date/time formats
- Repair missing or inconsistent values
- Normalize addresses and city/borough fields

### 2.2 Data Enrichment
- FIRST_ORDER_DATE
- ORDER_TOTAL_MINUTES
- TOTAL_MILES_TRAVELLED (Haversine-based)
- COMPLETE_COORDS (lat/long)
- Standardized operating hours with overnight handling

### 2.3 Schema Refinement
- Drop redundant or unused columns
- Rename fields for consistency
- Cast numeric/string/date types as needed

---
## 3. Silver Table Documentation

### 3.1 SILVER_CUSTOMER
Derived from: bronze_customer + bronze_orders

#### Purpose
Creates a clean, enriched customer dimension including each customer’s first ever order.

#### Key Transformations
- Extract earliest order timestamp from orders CTE
- Add FIRST_ORDER_DATE
- Cast DOB and dates correctly
- Produce one row per customer

#### Schema
| Column | Type | Description |
|--------|------|-------------|
| CUSTOMER_ID | NUMBER | Unique customer ID |
| FIRST_NAME | VARCHAR | Cleaned name |
| LAST_NAME | VARCHAR | Cleaned name |
| EMAIL_ADDRESS | VARCHAR | Email |
| DATE_OF_BIRTH | DATE | Birth date |
| FIRST_ORDER_DATE | DATE | First order |
| MEMBERSHIP_TYPE | VARCHAR | Loyalty tier |

---
### 3.2 SILVER_RIDER
Derived from: bronze_rider

#### Purpose
Provides a reliable rider dimension, correcting delivery methods, dates, and addresses.

#### Key Transformations
- Format JOIN_DATE
- Set missing PRIMARY_DELIVERY_METHOD → 'bicycle'
- Remove leading zeros from ADDRESS
- Type enforcement

#### Schema
| Column | Type |
|--------|------|
| RIDER_ID | NUMBER |
| FIRST_NAME | VARCHAR |
| LAST_NAME | VARCHAR |
| DOB | DATE |
| PRIMARY_DELIVERY_METHOD | VARCHAR |
| EMPLOYEE_ID | VARCHAR |
| ADDRESS | VARCHAR |
| JOIN_DATE | DATE |

---
### 3.3 SILVER_RESTAURANT
Derived from: bronze_restaurant

#### Purpose
Produces a normalized restaurant table with correct coordinates, boroughs, and operating hours.

#### Key Transformations
- Generate COMPLETE_COORDS = "lat,long"
- Cast ZIP_CODE → INT
- Normalize borough rules
- Standardize operating hours including overnight
- Drop redundant columns

#### Schema (key fields)
| Column | Type |
|--------|------|
| RESTAURANT_ID | NUMBER |
| RESTAURANT_NAME | VARCHAR |
| AREA | VARCHAR |
| CATEGORIES | VARCHAR |
| OPERATING_HOURS_MON–SUN | VARCHAR |
| FOOD_RATING | FLOAT |
| SERVICE_RATING | FLOAT |
| VALUE_RATING | FLOAT |
| AVG_PLATFORM_RATING | FLOAT |
| AVG_EXPERIENCE_RATING | FLOAT |
| COMPLETE_COORDS | VARCHAR |
| ZIP_CODE | NUMBER |
| BOROUGH | VARCHAR |

---
### 3.4 SILVER_ORDERS
Derived from: bronze_orders + silver_rider + silver_restaurant

#### Purpose
Creates a fully enriched transactional fact table with delivery times and distance metrics.

#### Key Transformations
- Join rider + restaurant enrichment
- Haversine distance calculation
- Compute ORDER_TOTAL_MINUTES
- Set missing rider_vehicle → 'bicycle'
- Normalize timestamps

#### Schema (key fields)
| Column | Type |
|--------|------|
| ORDER_ID | NUMBER |
| CUSTOMER_ID | NUMBER |
| RESTAURANT_ID | NUMBER |
| RIDER_ID | NUMBER |
| STATE | VARCHAR |
| ORDER_TOTAL | NUMBER |
| DISCOUNT | NUMBER |
| ORDER_TIME / PICKUP_TIME / DELIVERY_TIME | TIMESTAMP |
| ORDER_TOTAL_MINUTES | NUMBER |
| DELIVERY_COORDS | VARCHAR |
| TOTAL_MILES_TRAVELLED | FLOAT |
| RIDER_PAYMENT | VARCHAR |
| RIDER_VEHICLE | VARCHAR |

---
## 4. Clean‑and‑Tidy Pipeline (Supporting Silver)
Ensures: 
- Bronze tables exist and are structured correctly
- Placeholder rows added to prevent dashboard failures
- Whitespace, casing, null handling standardization
- Early data quality enforcement

---
## 5. Data Lineage Diagram
```
BRONZE → SILVER → CLEAN & TIDY → GOLD
```

---
## 6. Summary
The Silver layer is responsible for:
- Cleaning and standardizing raw Bronze data
- Adding business logic enrichments
- Creating high‑quality dimensions and facts
- Ensuring downstream systems run smoothly

