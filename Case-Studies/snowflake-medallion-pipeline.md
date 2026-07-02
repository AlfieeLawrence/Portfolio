# Case Study: Snowflake Medallion Architecture Pipeline

**Role:** Data & AI Consultant, Kubrick Group  
**Tech Stack:** Snowflake, SQL Server (AWS EC2), Azure Blob Storage, Azure DevOps, Python, PySpark, Power BI  
**Architecture Diagram:** [`Assets/diagrams/medallion-architecture.md`](../Assets/diagrams/medallion-architecture.md)  
**Project Documentation:** [`Projects/Snowflake_Medallion_Architecture_Pipeline`](../Projects/Snowflake_Medallion_Architecture_Pipeline/README.md)

---

## Background

A restaurant delivery client operated across multiple fragmented source systems — operational data held in a SQL Server on AWS EC2, order files landing in Azure Blob Storage, and no centralised analytics layer. Reporting was manual, inconsistent, and unable to support the business intelligence and forecasting capability the client needed to manage operations at scale.

As a Data & AI Consultant at Kubrick Group, I was engaged to design and deliver an end-to-end cloud data platform on Snowflake that would consolidate these sources, standardise data quality, and serve analytics-ready outputs to BI dashboards and machine learning workflows.

---

## What I Built

I designed and implemented a three-layer medallion architecture in Snowflake, fully automated from source ingestion through to Gold-layer reporting outputs.

**Bronze — Raw Ingestion**  
I built a high-throughput Python data loader that connected to SQL Server via Azure DevOps pipelines, performed chunked extraction with multi-threaded `PUT` operations, and loaded raw rider, customer, restaurant, and order data into Snowflake Bronze tables using `COPY INTO`. Orders from Azure Blob Storage were loaded separately via a Snowflake external stage with SAS credentials. A lightweight status flag mechanism (`STATUS_FLAGS`) decoupled ingestion from Snowflake processing, ensuring compute was only consumed when new data was available.

**Orchestration**  
A Snowflake Task polled the status flag on a configurable schedule and triggered a stored procedure (`RUN_IF_FLAGGED`) that conditionally executed the full downstream notebook sequence — Bronze, Silver, Clean & Tidy, and Sales Forecasting — before resetting the flag. This removed any manual intervention from the pipeline execution.

**Silver — Cleaning & Enrichment**  
The Silver layer produced four high-quality dimension and fact tables: `SILVER_CUSTOMER`, `SILVER_RIDER`, `SILVER_RESTAURANT`, and `SILVER_ORDERS`. Transformations included Haversine distance calculations for delivery mileage, date standardisation, address normalisation, operating hours handling for overnight periods, and first-order attribution per customer. A Clean & Tidy pipeline enforced structural integrity and null handling before any Gold views executed.

**Gold — Analytics & Forecasting Outputs**  
The Gold layer delivered two families of analytics views:  
- *Customer & Order KPIs*: daily totals for orders, sales, new customers, and average pickup and delivery times — backed by a complete calendar spine with zero-fill for unbroken BI time-series.  
- *Rider Performance Awards*: active rider tracking, power rider identification, and four award categories (most deliveries, most travelled, big day, longest serving) using window functions and rolling date windows.  
- *Sales Forecasting Dataset*: a feature-engineered fact table (`SALESFORCASTDATA`) joining Silver data and adding day-of-week, time-of-day, season, and restaurant/customer context — ready for ML model consumption.

A separate API enrichment pipeline (Azure DevOps + Geoapify) reverse-geocoded restaurant coordinates and loaded enriched location metadata into Snowflake as a reusable lookup.

---

## Challenges

**Schema drift across SQL Server tables** was handled by instrumenting the loader with `INFORMATION_SCHEMA` introspection, dynamically mapping source types to Snowflake equivalents and using `CREATE OR REPLACE` on Bronze tables at each run.

**Decoupling cost from latency** was the motivation for the status flag design. Rather than polling Snowflake compute continuously, the Task only triggers a real processing run when the Azure DevOps pipeline has confirmed a successful Bronze load — minimising idle warehouse time.

**Cross-source data quality** was addressed with the Clean & Tidy pipeline, which ran after Silver processing to catch nulls, add structural placeholder rows, and standardise casing and whitespace before downstream Gold views ran.

---

## Outcomes

- Fully automated end-to-end pipeline from raw source ingestion to analytics-ready Gold views, removing all manual data preparation steps.
- Power BI dashboards and rider award views delivered directly from governed, reproducible Gold-layer outputs.
- ML-ready `SALESFORCASTDATA` table with temporal and contextual feature engineering supporting predictive modelling use cases.
- Modular, well-documented architecture allowing new sources, outputs, or processing stages to be added without redesigning the pipeline.

> *Note: Replace or extend this section with specific client metrics, volume numbers, or performance improvements once cleared for sharing.*

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Status flag trigger mechanism | Decouples ingestion latency from Snowflake compute cost |
| Full Bronze refresh per run | Ensures idempotency; simplifies schema drift handling |
| Stored procedure + Task orchestration | Native Snowflake tooling — no external scheduler required |
| Calendar spine + zero-fill in Gold | Guarantees continuous time-series for BI; avoids gaps in dashboard charts |
| Clean & Tidy stage between Silver and Gold | Acts as a data quality gate before any reporting or ML output is produced |
| Independent API enrichment pipeline | Decouples geocoding from the main ingestion trigger; can run on its own schedule |
