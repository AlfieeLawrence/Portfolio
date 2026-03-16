# database_name – Data Pipeline Orchestration (Overview)

## 1. Purpose of This Document
This document provides an overview of the **data flow pipeline** connecting Azure DevOps and Snowflake. It explains how the Azure ingestion pipeline triggers Snowflake processing using a simple status flag, a stored procedure, and a scheduled Snowflake Task.

Each processing stage (Bronze, Silver, Clean & Tidy, Forecasting) has its own dedicated documentation, and this intro file acts as the master reference.

---

## 2. High-Level Pipeline Flow
```
Azure DevOps (SQL → Snowflake Loader)
    │
    │ sets datainflag = 1
    ▼
Snowflake.STATUS_FLAGS
    │ Task checks flag
    ▼
Stored Procedure RUN_IF_FLAGGED()
    │ if flag = 1
    ▼
Executes notebooks:
   1. BRONZE_COMPLETE()
   2. SILVER_COMPLETE()
   3. CLEANANDTIDY()
   4. SALESFORCASTING()
    │
    ▼
Flag reset to 0
```

---

## 3. Status Flag Table
The status flag is the hand‑off mechanism between Azure DevOps and Snowflake.

```sql
USE DATABASE database_name;
USE SCHEMA schema_name;

CREATE OR REPLACE TABLE status_flags (
    datainflag INTEGER NOT NULL
);

INSERT INTO status_flags VALUES (0);
```

### Meaning of `datainflag`
| Value | Meaning |
|-------|---------|
| **0** | No new data available; Snowflake should not run |
| **1** | New Bronze data loaded by Azure DevOps; Snowflake should run |

Azure DevOps sets the flag to **1** upon successful completion of ingestion.

---

## 4. Stored Procedure: `RUN_IF_FLAGGED`
This stored procedure conditionally triggers all downstream Snowflake processing depending on the value of the flag.

```sql
CREATE OR REPLACE PROCEDURE database_name.schema_name.RUN_IF_FLAGGED()
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE v_flag INTEGER;
BEGIN
    SELECT datainflag INTO :v_flag
    FROM database_name.schema_name.STATUS_FLAGS;

    IF (v_flag = 1) THEN

        -- Run Bronze notebook
        EXECUTE NOTEBOOK database_name.schema_name.BRONZE_COMPLETE();

        -- Run Silver notebook
        EXECUTE NOTEBOOK database_name.schema_name.SILVER_COMPLETE();

        -- Run Clean & Tidy notebook
        EXECUTE NOTEBOOK database_name.schema_name.CLEANANDTIDY();

        -- Run Sales Forecasting notebook
        EXECUTE NOTEBOOK database_name.schema_name.SALESFORCASTING();

        -- Reset flag
        UPDATE database_name.schema_name.STATUS_FLAGS
        SET datainflag = 0;

        RETURN 'Flag was 1 → executed notebook sequence + reset to 0';
    ELSE
        RETURN 'Flag was 0 → skipped';
    END IF;

END;
$$;
```

### Behaviour Summary
- If flag = **1** → run entire Snowflake pipeline + reset to 0.
- If flag = **0** → do nothing.

---

## 5. Snowflake Task: Automated Checking
The Task continuously checks the flag and triggers the stored procedure.

```sql
CREATE OR REPLACE TASK t_check_flag_every_xm
  WAREHOUSE = COMPUTE_WH
  SCHEDULE = 'x MINUTE'
AS
  CALL run_if_flagged();
```

**Start the Task:**
```sql
ALTER TASK t_check_flag_every_xm RESUME;
```

### Scheduling Options
- `1 MINUTE` – near‑real‑time triggering
- `5 MINUTE` – common balance between latency & cost
- `CRON` expressions – full scheduling flexibility

---

## 6. How Azure DevOps Triggers the Snowflake Pipeline
Your SQL → Snowflake pipeline ends with:

```sql
UPDATE status_flags
SET datainflag = 1;
```

This signals Snowflake that new Bronze data is ready, enabling the rest of the pipeline to execute automatically.

---

## 7. Links to Processing Stage Documentation
Once added, these docs will be linked here:

### 🔶 Bronze Layer
Raw ingestion from SQL Server & Azure Blob.  
➡ `/docs/bronze.md`

### 🔷 Silver Layer
Standardisation, cleansing, conformance.  
➡ `/docs/silver.md`

### 🧹 Restaurant Data Quality
Downstream cleanup and structural hygiene.  
➡ `Restaurant Data Quality Documentation.docx`

### 📈 Sales Forecasting
ML-ready processed forecasting data pipeline.  
➡ `/docs/forecasting.md`

### 🟡 Gold Layer
Creation of views for Dashboard and analytics, each file explained individually.  
➡ `/docs/Gold`

---

## 8. Summary
The framework provides:
- Clean separation of ingestion (Azure) vs the ingestion and transformation (Snowflake)
- A simple, reliable flag-based trigger mechanism
- Automatic end‑to‑end execution when new Bronze data arrives
- Modular expansion for future processing stages

This document acts as the entry point for the full database_name data pipeline.