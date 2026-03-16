
# Snowflake Medallion Architecture Pipeline — Project README

## ❄️ Overview
This project implements a full end‑to‑end data platform using Snowflake, Azure DevOps, and Python/SQL, following a modern Medallion Architecture.

It includes:
- Multi-source ingestion (SQL Server + Azure Blob Storage)
- Bronze, Silver, and Gold transformation layers
- Clean/Tidy standardisation layer
- Machine-learning‑ready Forecasting Layer
- Curated BI views for Customer, Order, and Rider performance
- A standalone API enrichment pipeline
- A fully automated orchestration mechanism using Tasks + Stored Procedure

All supporting documentation is included inside the projects documentation folder.

## 🏗️ Architecture
```
          SQL Server                         Azure Blob
             |                                     |
             |                                     |
             v                                     v
      Azure DevOps Pipeline (Python Loader + CSV)  |
             |                                     |
             v                                     |
            Bronze (Raw Landing Tables) <-----------
             |
             v
         Silver Layer (Cleaned & Enriched)
             |
             v
     Clean & Tidy (Standardisation Layer)
             |
             v
      Forecasting Layer (ML Features)
             |
             v
      Gold Layer (Customer, Order & Rider Views)
             |
             v
      BI Dashboards / Analytics / ML Models
```

## 🔄 Pipeline Orchestration (Flag-Based)
Azure DevOps sets a status flag when ingestion completes. Snowflake tasks run regularly and execute the full pipeline when the flag is set.

## 🟫 Bronze Layer — Raw Ingestion
See `/docs/bronze.md`.

## 🥈 Silver Layer — Clean & Enriched Data
See `/docs/silver.md`.

## 📈 Forecasting Layer — ML Feature Engineering
See `/docs/forecasting.md`.

## 🟧 Gold Layer — Curated Business Views
Includes Customer & Order KPIs and Rider Awards dashboards.

See `/docs/Customer&OrderGold.md` and `/docs/RiderAwardsGold.md`.

## 🟪 API Enrichment Pipeline
See `/docs/pipeline_api_enrichment.md`.

## 🧑‍💻 My Contributions
- Unified all components into a single orchestrated pipeline
- Built Bronze ingestion and Silver transformation logic
- Implemented SQL Server → Snowflake ingestion via Azure DevOps
- Contributed to API enrichment pipeline
- Wrote all documentation
- Helped design dashboard layouts and filtering

## ⚠️ Limitations & Decisions
- Snowflake trial restricted API usage and SQL Server connectors
- Only 500 credits available → careful compute management
- Limited warehouse sizes + concurrency led to portable pipeline design
- Git repo used to move code across multiple trial accounts

## 📚 Documentation References
- `/docs/bronze.md`
- `/docs/silver.md`
- `/docs/forecasting.md`
- `/docs/Customer&OrderGold.md`
- `/docs/RiderAwardsGold.md`
- `/docs/pipeline_overview.md`
- `/docs/pipeline_api_enrichment.md`

