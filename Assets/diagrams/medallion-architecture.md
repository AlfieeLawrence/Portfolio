# Medallion Architecture — Snowflake Pipeline

Architecture diagram for the end-to-end Snowflake medallion data pipeline.  
Full project documentation: [`Projects/Snowflake_Medallion_Architecture_Pipeline`](../../Projects/Snowflake_Medallion_Architecture_Pipeline/README.md)

---

```mermaid
flowchart TD

    subgraph SOURCES["Data Sources"]
        SQL["SQL Server\n(AWS EC2)\nRiders · Customers · Restaurants"]
        BLOB["Azure Blob Storage\nOrders (CSV files)"]
        GEOAPI["Geoapify API\nReverse-Geocoding\n& Place Details"]
    end

    subgraph INGESTION["Ingestion — Azure DevOps"]
        AZP_SQL["Azure Pipeline\nsql-sf.yml\nManual / Scheduled"]
        PYLOADER["Python Loader\nload_sql_to_snowflake.py\nSchema introspection → chunked SELECT\n→ parallel PUT → COPY INTO"]
        EXTST["Snowflake External Stage\norderr data via SAS token\n→ COPY INTO BRONZE_ORDERS"]
        AZP_API["Azure Pipeline\napilocation.yml\napiazurepre.py\nSQL Server → API → Snowflake"]
    end

    subgraph BRONZE["🔶 Bronze Layer — Raw Landing (Snowflake)"]
        BR["BRONZE_RIDER"]
        BC["BRONZE_CUSTOMER"]
        BRES["BRONZE_RESTAURANT"]
        BO["BRONZE_ORDERS"]
        FLAG["STATUS_FLAGS\ndatainflag = 1"]
    end

    subgraph ORCH["Orchestration — Snowflake"]
        TASK["Snowflake Task\nt_check_flag_every_xm\n(polls flag on schedule)"]
        PROC["Stored Procedure\nRUN_IF_FLAGGED()\nconditionally triggers notebooks"]
    end

    subgraph SILVER["🔷 Silver Layer — Clean · Enrich · Standardise"]
        SC["SILVER_CUSTOMER\nfirst order date · DOB cast"]
        SR["SILVER_RIDER\ndelivery method · address clean"]
        SRES["SILVER_RESTAURANT\ncoordinates · boroughs · hours"]
        SO["SILVER_ORDERS\nHaversine distance · order duration"]
        CT["Clean & Tidy Pipeline\ndata quality · null enforcement\nplaceholder rows"]
    end

    subgraph GOLD["🟡 Gold Layer — Analytics-Ready Outputs"]
        direction LR
        GCO["Customer & Order Views\nTOTAL_ORDERS\nTOTAL_SALES\nNEW_CUSTOMERS\nAVG_PICKUP_TIME\nAVG_DELIVERY_TIME\n(calendar spine + zero-fill)"]
        GRA["Rider Award Views\nACTIVE_RIDERS\nPOWER_RIDERS\nMOST_DELIVERIES_AWARD\nMOST_TRAVELLED_AWARD\nBIG_DAY_AWARD\nLONGEST_SERVING_AWARD"]
        GF["Sales Forecasting Dataset\nSALESFORCASTDATA\nFeature engineering:\nday of week · time of day\nseason · ratings · membership · borough"]
    end

    subgraph OUTPUTS["Downstream Consumers"]
        PBI["Power BI Dashboards\nKPI reporting"]
        ML["ML / Forecasting Models\npredictive modelling"]
    end

    %% Ingestion flows
    SQL --> AZP_SQL
    BLOB --> AZP_SQL
    AZP_SQL --> PYLOADER
    PYLOADER -->|"COPY INTO (SQL Server tables)"| BR
    PYLOADER -->|"COPY INTO"| BC
    PYLOADER -->|"COPY INTO"| BRES
    AZP_SQL --> EXTST
    EXTST -->|"COPY INTO"| BO
    PYLOADER -->|"datainflag = 1"| FLAG

    %% API enrichment (independent pipeline)
    SQL -->|"lat / long"| AZP_API
    GEOAPI --> AZP_API
    AZP_API -->|"write_pandas()"| SRES

    %% Orchestration
    FLAG -->|"Task polls flag"| TASK
    TASK --> PROC

    %% Procedure triggers notebooks
    PROC -->|"BRONZE_COMPLETE notebook"| BR
    PROC -->|"SILVER_COMPLETE notebook"| SC
    PROC -->|"SILVER_COMPLETE notebook"| SR
    PROC -->|"SILVER_COMPLETE notebook"| SO
    PROC -->|"CLEANANDTIDY notebook"| CT
    PROC -->|"SALESFORCASTING notebook"| GF
    PROC -->|"flag reset → 0"| FLAG

    %% Bronze to Silver
    BR --> SC
    BC --> SC
    BR --> SR
    BRES --> SRES
    BO --> SO
    SR --> SO
    SRES --> SO

    %% Silver to clean & tidy
    SC --> CT
    SR --> CT
    SRES --> CT
    SO --> CT

    %% Silver/clean to Gold
    CT --> GCO
    CT --> GRA
    SC --> GF
    SRES --> GF
    SO --> GF

    %% Gold to outputs
    GCO --> PBI
    GRA --> PBI
    GF --> ML
```

---

## Key Design Decisions

| Pattern | Implementation |
|---|---|
| Idempotent Bronze loads | `CREATE OR REPLACE TRANSIENT TABLE` — full refresh per run |
| Decoupled ingestion trigger | `STATUS_FLAGS` table with `datainflag` flag |
| Automated Snowflake processing | Snowflake Task → `RUN_IF_FLAGGED()` stored procedure → notebook chain |
| Enrichment separation | API enrichment pipeline runs independently, does not modify status flags |
| Data quality gate | Clean & Tidy stage between Silver and Gold enforces null handling and structural integrity |
| Calendar continuity | Gold views use date spine with zero-fill to ensure unbroken time-series for BI |
