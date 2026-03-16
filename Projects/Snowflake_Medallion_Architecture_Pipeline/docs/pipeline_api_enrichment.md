
# database_name – API Enrichment Pipeline (SQL → API → Snowflake)

## 1. Purpose of This Document
This document describes the **API Enrichment Pipeline**, an Azure DevOps–driven process that:

1. Pulls restaurant coordinates from **SQL Server**
2. Calls **Geoapify** reverse‑geocoding + place‑details APIs
3. Constructs enriched restaurant metadata
4. Loads the final dataset into **Snowflake** (default table: `schema_name.RESTAURANT_API_RESULTS`)

This pipeline runs independently from the Bronze→Silver workflow and **does not use the Snowflake flag mechanism**. It is a standalone enrichment process.

---

## 2. High-Level Flow
```
SQL Server (schema_name.restaurants)
        │
        ▼
Extract: RESTAURANT_ID, LATITUDE, LONGITUDE
        │
        ▼
Geoapify Reverse-Geocoding API
Geoapify Place Details API
        │
        ▼
Enriched Restaurant Metadata
(name, address, postcode, website, phone, hours, wheelchair access, …)
        │
        ▼
Snowflake Table:
schema_name.RESTAURANT_API_RESULTS
```

---

## 3. Azure DevOps Pipeline Definition
File: `apilocation.yml`

### Key Features
- Windows agent with **ODBC Driver 18** (installed if missing)
- Python 3.11 runtime
- Installs API + Snowflake dependencies
- Runs **only** `scripts/apiazurepre.py`
- Writes directly into Snowflake via `write_pandas()`

---

## 4. Pipeline YAML (Annotated)

```yaml
trigger: none
pr: none

pool:
  vmImage: 'windows-latest'

variables:
  # --- SQL Server ---
  SqlServerHost: 'Host'
  SqlDatabase:   'database_name'
  Encrypt:       'True'
  TrustCert:     'True'

  # --- Snowflake context ---
  SfAccount:   'Account_Identifier'
  SfUser:      'User'
  SfRole:      'Ingestion_Role'
  SfWarehouse: 'COMPUTE_Warehouse'
  SfDatabase:  'database_name'
  SfSchema:    'schema_name'

  # Output table (optional override)
  TargetTable: 'RESTAURANT_API_RESULTS'

# Secrets to define (mark as secret):
#   SqlUser, SqlPass, SfPassword, GeoApiKey

stages:
- stage: RunAPIOnly
  displayName: Run API Enrichment (SQL -> API -> Snowflake)
  jobs:
  - job: RunApiJob
    displayName: Run apiazurepre.py
    steps:

    # 1) Use Python 3.11
    - task: UsePythonVersion@0
      displayName: Use Python 3.11
      inputs:
        versionSpec: '3.11'

    # 2) Ensure Microsoft ODBC Driver 18 for SQL Server
    - powershell: |
        $ErrorActionPreference = 'Stop'
        $drv = Get-OdbcDriver | Where-Object { $_.Name -eq 'ODBC Driver 18 for SQL Server' }
        if (-not $drv) {
          Write-Host "Installing ODBC Driver 18..."
          winget source update
          winget install -e --id Microsoft.msodbcsql.18 --silent --accept-source-agreements --accept-package-agreements
        } else {
          Write-Host "ODBC Driver 18 already installed."
        }
      displayName: Ensure ODBC Driver 18

    # 3) Install Python dependencies
    - script: |
        python -m pip install --upgrade pip
        python -m pip install pyodbc pandas sqlalchemy snowflake-connector-python[pandas] requests
      displayName: Install Python dependencies

    # 4) Run ONLY the API enrichment script
    - script: python scripts/apiazurepre.py
      displayName: Run apiazurepre.py
      env:
        # --- SQL Server (source) ---
        SQL_HOST: $(SqlServerHost)
        SQL_DB:   $(SqlDatabase)
        SQL_USER: $(SqlUser)
        SQL_PASS: $(SqlPass)
        SQL_ENCRYPT: $(Encrypt)
        SQL_TRUST: $(TrustCert)

        # Optional overrides
        # SQL_SRC_QUERY: SELECT restaurant_id AS RESTAURANT_ID, latitude AS LATITUDE, longitude AS LONGITUDE FROM restaurant.restaurants
        # SQL_SRC_TABLE: restaurant.restaurants

        # --- Geoapify API key ---
        GEO_API_KEY: $(GeoApiKey)

        # --- Snowflake (destination) ---
        SF_ACCOUNT:  $(SfAccount)
        SF_USER:     $(SfUser)
        SF_PASSWORD: $(SfPassword)
        SF_ROLE:     $(SfRole)
        SF_WH:       $(SfWarehouse)
        SF_DB:       $(SfDatabase)
        SF_SCHEMA:   $(SfSchema)

        # --- Target table name ---
        TARGET_TABLE: $(TargetTable)
```

---

## 5. Enrichment Script (`scripts/apiazurepre.py`)

### Responsibilities
1. **Load restaurants from SQL Server**
   - Default source: `schema_name.restaurants` (columns: `restaurant_id`, `latitude`, `longitude`)
   - Custom overrides via `SQL_SRC_QUERY` or `SQL_SRC_TABLE`
   - Uses `sqlalchemy` + ODBC 18

2. **Call Geoapify APIs with retry/backoff**
   - `GET https://api.geoapify.com/v1/geocode/reverse`
   - `GET https://api.geoapify.com/v2/place-details`
   - Retries on `429/500/502/503/504`, exponential backoff (configurable via env)

3. **Parse API responses & construct features**
   - Address components: name, number, street, suburb, city, postcode, country
   - Other details: phone, website, opening hours, wheelchair access
   - Address normalisation rule example: `New York` → `Ny` (as per current logic)

4. **Build output DataFrame**
   Final columns:
   ```
   RESTAURANT_ID, RESTAURANT_NAME, ADDRESS,
   ZIP_CODE, SUBURB, CITY, STREET, COUNTRY,
   PHONE, WEBSITE, HOURS, WHEELCHAIR
   ```

5. **Load to Snowflake**
   - Uses `snowflake.connector.pandas_tools.write_pandas()`
   - `auto_create_table=True` creates the table on first run
   - `overwrite=True` replaces existing content (can be adjusted to append)

---

## 6. Snowflake Target Table

### Default Target
`schema_name.RESTAURANT_API_RESULTS` (configurable via `TARGET_TABLE`)

### Expected Schema (auto‑inferred)
| Column | Type | Notes |
|---|---|---|
| RESTAURANT_ID | STRING | Source system ID |
| RESTAURANT_NAME | STRING | From reverse-geocoding result |
| ADDRESS | STRING | Combined street/suburb line |
| ZIP_CODE | STRING | Postcode/ZIP |
| SUBURB | STRING | Neighborhood |
| CITY | STRING | City (note: example normalisation to `Ny`) |
| STREET | STRING | Street name |
| COUNTRY | STRING | Country |
| PHONE | STRING | Business contact |
| WEBSITE | STRING | Business website |
| HOURS | STRING | Opening hours (raw string) |
| WHEELCHAIR | STRING | Accessibility indicator |

> **Note:** Types are inferred from pandas → Snowflake mapping; if stricter typing is required, create the table ahead of time with explicit column types.

---

## 7. Configuration & Environment Variables

### Required (Secrets)
- `SqlUser`, `SqlPass`, `SfPassword`, `GeoApiKey`

### SQL Server
- `SQL_HOST`, `SQL_DB`, `SQL_USER`, `SQL_PASS`, `SQL_ENCRYPT`, `SQL_TRUST`
- Optional: `SQL_SRC_QUERY`, `SQL_SRC_TABLE`

### Geoapify API
- `GEO_API_KEY`
- Optional tuning: `API_TIMEOUT` (default 30), `API_MAX_RETRIES` (default 3), `API_BACKOFF_SECS` (default 1.0)

### Snowflake
- `SF_ACCOUNT`, `SF_USER`, `SF_PASSWORD`, `SF_DB`, `SF_SCHEMA`
- Optional: `SF_ROLE`, `SF_WH`, `TARGET_TABLE`

---

## 8. Operational Considerations
- **Idempotency**: current load uses `overwrite=True` when writing—each run replaces prior data.
- **Resilience**: API calls include retry/backoff; non‑200 non‑retryable responses are recorded as best‑effort.
- **Missing data**: if API returns no result, address fields are filled with placeholders (`"incorrect address"`, etc.).
- **Performance**: sequential API calls keep rate‑limit friendly. Future optimisation could add limited parallelism.

---

## 9. Relationship to Main (Flag‑Based) Pipeline
- This pipeline **does not** modify `STATUS_FLAGS` and **does not** trigger `RUN_IF_FLAGGED()`.
- It can be run on its own schedule (or manually) without affecting Bronze/Silver processing.
- Downstream layers (e.g., Silver/Gold/ML) can consume `RESTAURANT_API_RESULTS` as a lookup/enrichment table.

---

## 10. Links & Next Steps
- **Main Pipeline Overview:** `/docs/pipeline_overview.md`
- **Bronze Layer:** `/docs/bronze.md`
- **Silver Layer** : `/docs/silver.md`
- **Gold Layer** : `/docs/Gold`
- **Sales Forecasting** : `/docs/Forecasting.md`
- **Restaurant Data Quality** : `/docs/Restaurant Data Quality Documentation.docx`




