
# Bronze Layer Documentation

**Scope:** End-to-end ingestion of raw operational data into Snowflake **Bronze** tables from two sources:

1) **SQL Server → Snowflake** via Azure DevOps pipeline utalising a high-throughput Python loader (fast `PUT` + `COPY INTO`).
2) **Azure Blob Storage → Snowflake** via Snowflake external stage and `COPY INTO` (orders data landing).

**Applies to:**
- Azure DevOps (`SQL-SF.yml`)
- Python script (`scripts/load_sql_to_snowflake.py`)
- Snowflake (database: `<SNOWFLAKE_DATABASE>`, schema: `<SNOWFLAKE_SCHEMA>`)

---

## 1) Purpose of Bronze

The **Bronze layer** captures **raw, unmanipulated and non cleansed** source data with **minimal transformation**, preserving source fidelity and enabling replayable, idempotent loads. It is the landing zone that feeds Silver (standardized/cleaned) and Gold (curated/agrigated) layers.

---

## 2) Sources & Targets

### Sources
- **SQL Server**
  - Host: `<SQL_SERVER_HOST>`
  - Database: `<SQL_SERVER_DATABASE>`
  - Tables: `<SQL_SERVER_SCHEMA>.riders`, `<SQL_SERVER_SCHEMA>.customers`, `<SQL_SERVER_SCHEMA>.restaurants`

- **Azure Blob Storage (orders)**
  - Account/Container Path: `azure://<STORAGE_ACCOUNT>.blob.core.windows.net/<CONTAINER_OR_PATH>`

### Snowflake Targets
- **Account:** `<SNOWFLAKE_ACCOUNT>`
- **Role:** `<SNOWFLAKE_ROLE>` (recommended to replace with least-privilege role for prod)
- **Warehouse:** `<SNOWFLAKE_WAREHOUSE>`
- **Database/Schema:** `<SNOWFLAKE_DATABASE>.<SNOWFLAKE_SCHEMA>`
- **Table Type:** `TRANSIENT` (configurable)

**Bronze tables (auto-created/managed):**
- `<SNOWFLAKE_SCHEMA>.BRONZE_RIDER`
- `<SNOWFLAKE_SCHEMA>.BRONZE_CUSTOMER`
- `<SNOWFLAKE_SCHEMA>.BRONZE_RESTAURANT`
- `<SNOWFLAKE_SCHEMA>.BRONZE_ORDERS` (from Azure Blob)

---

## 3) Architecture & Flow (High Level)

```text
A) SQL Server → Snowflake
   SQL Server (<SQL_SERVER_DATABASE>)
     ⭢ Chunked SELECT via SQLAlchemy/pyodbc
     ⭢ CSV files (normalized headers)
     ⭢ Multi-threaded PUT to @~/<dst> (temp_files) to user stage
     ⭢ COPY INTO <DB>.<SCHEMA>.<BRONZE_TABLE> (CSV file format)
     ⭢ PURGE staged files post-load
     ⭢ Update status flag (best-effort)

B) Azure Blob → Snowflake
   Azure Blob Storage (<STORAGE_ACCOUNT>/<CONTAINER_OR_PATH>)
     ⭢ Snowflake FILE FORMAT (CSV)
     ⭢ Snowflake EXTERNAL STAGE (SAS creds)
     ⭢ CREATE OR REPLACE TABLE <SNOWFLAKE_SCHEMA>.BRONZE_ORDERS (typed columns)
     ⭢ COPY INTO from @<SNOWFLAKE_SCHEMA>.ORDERDATA with explicit mapping, file metadata, timestamp
```

---

## 4) SQL Server → Snowflake (Azure DevOps Pipeline)

**Pipeline file:** `SQL-SF.yml` (manual/scheduled trigger)

**Key capabilities:**
- Ensures **ODBC Driver 18** for SQL Server on the runner
- Uses **Python 3.11**, cached pip deps (`pyodbc`, `pandas`, `sqlalchemy`, `snowflake-connector-python`)
- Executes `scripts/load_sql_to_snowflake.py`
- Passes configuration via environment variables (including a JSON `TABLE_MAP`)

**Source → Destination Map (example):**
```json
[
  {"src": "<SQL_SERVER_SCHEMA>.riders", "dst": "BRONZE_RIDER"},
  {"src": "<SQL_SERVER_SCHEMA>.customers", "dst": "BRONZE_CUSTOMER"},
  {"src": "<SQL_SERVER_SCHEMA>.restaurants", "dst": "BRONZE_RESTAURANT"}
]
```

### Loader script highlights (`load_sql_to_snowflake.py`)
- **Schema introspection** from SQL Server (`INFORMATION_SCHEMA.COLUMNS`) and **type mapping** to Snowflake
- **Table (re)creation** as `TRANSIENT` (or `TEMPORARY` per `SF_TABLE_KIND`)
- **Chunked extraction** (rows per chunk are auto-tuned by table size)
- **Parallel `PUT`** with worker threads and Snowflake `PARALLEL=8`
- **`COPY INTO`** using a shared CSV file format, `PURGE=TRUE`, `ON_ERROR=CONTINUE`
- **Status flag** update (UPDATE STATUS_FLAGS SET datainflag = 1;) at end of run

> **TOTAL REFRESH:** Each run uses *create-or-replace* on Bronze tables; it is a **full refresh** of the data for these sources.

---

## 5) Azure Blob → Snowflake (Orders)

This path lands orders CSVs from Azure Blob Storage to `<SNOWFLAKE_SCHEMA>.BRONZE_ORDERS` using a Snowflake **external stage**.

### a) Create/ensure a CSV file format
```sql
CREATE OR REPLACE FILE FORMAT <SNOWFLAKE_SCHEMA>.CSV_FF
  TYPE = CSV
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  NULL_IF = ('', 'NULL');
```

### b) Create/ensure an external stage (SAS credentials)
```sql
CREATE OR REPLACE STAGE <SNOWFLAKE_SCHEMA>.ORDERDATA
  URL = 'azure://<STORAGE_ACCOUNT>.blob.core.windows.net/<CONTAINER_OR_PATH>'
  CREDENTIALS = (AZURE_SAS_TOKEN = '<SAS_TOKEN>')
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'order data MM';
```

> **Security note:** For production, consider using a **Storage Integration** instead of embedding SAS; it centralizes credentials and enables tighter governance, sored in a snowflake secret.

### c) Create/replace the target Bronze table
```sql
CREATE OR REPLACE TRANSIENT TABLE <SNOWFLAKE_SCHEMA>.BRONZE_ORDERS (
  IDX                NUMBER,
  ORDER_ID           STRING,
  RESTAURANT_ID      STRING,
  RIDER_ID           STRING,
  CUSTOMER_ID        STRING,
  ORDER_TOTAL        NUMBER(10,2),
  DISCOUNT           NUMBER(10,2),
  STATE              STRING,
  ORDER_TIME         TIMESTAMP_NTZ,
  PICKUP_TIME        TIMESTAMP_NTZ,
  DELIVERY_TIME      TIMESTAMP_NTZ,
  DELIVERY_LATITUDE  FLOAT,
  DELIVERY_LONGITUDE FLOAT,
  RIDER_VEHICLE      STRING,
  RIDER_PAYMENT      STRING,
  RIDER_TIP          NUMBER(10,2),
  APP_VERSION        STRING,
  DEVICE_TYPE        STRING,
  FILE_NAME          STRING,
  LOAD_TS            TIMESTAMP_NTZ
);
```

### d) Load data with `COPY INTO`
```sql
COPY INTO <SNOWFLAKE_SCHEMA>.BRONZE_ORDERS (
  IDX,
  ORDER_ID,
  RESTAURANT_ID,
  RIDER_ID,
  CUSTOMER_ID,
  ORDER_TOTAL,
  DISCOUNT,
  STATE,
  ORDER_TIME,
  PICKUP_TIME,
  DELIVERY_TIME,
  DELIVERY_LATITUDE,
  DELIVERY_LONGITUDE,
  RIDER_VEHICLE,
  RIDER_PAYMENT,
  RIDER_TIP,
  APP_VERSION,
  DEVICE_TYPE,
  FILE_NAME,
  LOAD_TS
)
FROM (
  SELECT
    t.$1::NUMBER                 AS IDX,
    t.$2::STRING                 AS ORDER_ID,
    t.$3::STRING                 AS RESTAURANT_ID,
    t.$4::STRING                 AS RIDER_ID,
    t.$5::STRING                 AS CUSTOMER_ID,
    t.$6::NUMBER(10,2)           AS ORDER_TOTAL,
    t.$7::NUMBER(10,2)           AS DISCOUNT,
    t.$8::STRING                 AS STATE,
    t.$9::TIMESTAMP_NTZ          AS ORDER_TIME,
    t.$10::TIMESTAMP_NTZ         AS PICKUP_TIME,
    t.$11::TIMESTAMP_NTZ         AS DELIVERY_TIME,
    t.$12::FLOAT                 AS DELIVERY_LATITUDE,
    t.$13::FLOAT                 AS DELIVERY_LONGITUDE,
    t.$14::STRING                AS RIDER_VEHICLE,
    t.$15::STRING                AS RIDER_PAYMENT,
    t.$16::NUMBER(10,2)          AS RIDER_TIP,
    t.$17::STRING                AS APP_VERSION,
    t.$18::STRING                AS DEVICE_TYPE,
    METADATA$FILENAME            AS FILE_NAME,
    CURRENT_TIMESTAMP()          AS LOAD_TS
  FROM @<SNOWFLAKE_SCHEMA>.ORDERDATA (FILE_FORMAT => <SNOWFLAKE_SCHEMA>.CSV_FF) AS t
)
ON_ERROR = 'CONTINUE';
```

> **Behavior notes**
> - `ON_ERROR = CONTINUE` loads valid rows and skips malformed ones.
> - `FORCE` defaults to `FALSE` so previously loaded files are skipped unless forced.
> - Use `PATTERN` to restrict to `*.csv` if the stage contains different file types.

### e) Status flag
In order to not trigger the pipeline when no data and waste compute resurces
```sql
UPDATE <SNOWFLAKE_SCHEMA>.STATUS_FLAGS SET DATAINFLAG = 0;
```
(Reset so that it can be updated back to 1 when new data is avalible and allows for a contious data updating pathway.)

---

## 6) Configuration Reference

### Environment variables (pipeline → script)
- **SQL Server:** `SQL_HOST`, `SQL_DB`, `SQL_USER` (secret), `SQL_PASS` (secret), `SQL_ENCRYPT`, `SQL_TRUST`
- **Snowflake:** `SF_ACCOUNT`, `SF_USER`, `SF_PASSWORD` (secret), `SF_ROLE`, `SF_WH`, `SF_DB`, `SF_SCHEMA`, `SF_TABLE_KIND`
- **Bronze control:** `STATUS_FLAGS_TABLE` (default `STATUS_FLAGS`), `TABLE_MAP` (JSON array)

### Snowflake objects (Blob path)
- File format: `<SNOWFLAKE_SCHEMA>.CSV_FF` (CSV, header skip, optional quotes, null handling)
- External stage: `<SNOWFLAKE_SCHEMA>.ORDERDATA` (SAS-based; consider Storage Integration for prod)
- Target table: `<SNOWFLAKE_SCHEMA>.BRONZE_ORDERS`

---

## 7) Security, Access & Governance
- Keep credentials in **Azure Pipelines secret variables**.
- In Snowflake, prefer a scoped **ingestor role** with: `USAGE` on WH/DB/Schema; `CREATE TABLE`, `CREATE/USE FILE FORMAT`, `PUT`, `COPY INTO`, and ownership on Bronze targets.
- For Blob ingestion, prefer **Storage Integration** over inline SAS for long-lived prod deployments.

---

## 8) Error Handling & Recovery
- **Driver/env issues**: pipeline ensures ODBC 18; failures are visible in step logs.
- **Schema drift**: tables recreated based on source schema per run.
- **COPY errors**: use `ON_ERROR = CONTINUE` and inspect `COPY_HISTORY` for rejected rows; tighten rules later if required.
- **Reruns**: SQL Server path is a full refresh; Blob path can be idempotent by skipping files unless `FORCE=TRUE`.

---

## 9) Runbook (Quick Steps)

**Run the SQL Server loader**
1. Open Azure DevOps → Pipelines → *SQL Server → Snowflake Loader*.
2. Set or verify secret variables.
3. Run and monitor steps.
4. Validate counts in `<SNOWFLAKE_SCHEMA>.BRONZE_*` tables.

**Run the Blob ingestion (orders)**
1. In Snowflake, ensure `<SNOWFLAKE_SCHEMA>.CSV_FF` and `<SNOWFLAKE_SCHEMA>.ORDERDATA` exist (or create as above).
2. Create (or replace) `<SNOWFLAKE_SCHEMA>.BRONZE_ORDERS`.
3. Execute the `COPY INTO` statement.
4. Optionally update status flags for automation and scheduling.

---

## 10) Change Log
- **v1.1** — Consolidated Bronze doc covering SQL Server & Azure Blob paths; added runbook and governance notes.
- **v1.0** — Initial Bronze documentation for SQL Server path.