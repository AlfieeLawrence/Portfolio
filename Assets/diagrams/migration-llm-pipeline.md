# Migration & LLM Conversion Pipeline

Architecture diagram for the AI-powered legacy SQL migration tool.  
This pipeline extracts SQL objects from a source data warehouse (Azure Synapse / SQL Server),
passes them to an LLM with a conversion prompt, and pushes the translated output to Databricks.

From CV: *"End-to-end migration of legacy warehouse assets from SQL Server and Azure Synapse into Databricks Delta Lake, engineering an AI-powered conversion tool to translate legacy SQL logic into PySpark and Delta Live Tables."*

---

```mermaid
flowchart TD

    subgraph SOURCE["Source Systems"]
        SYN["Azure Synapse / SQL Server\nLegacy Warehouse Assets"]
        OBJS["SQL Objects\n• Views\n• Stored Procedures\n• Functions"]
    end

    subgraph EXTRACT["Stage 1 — Extraction"]
        EXT["Extraction Script\n(Python)\nQueries INFORMATION_SCHEMA\n& sys.objects to enumerate objects\nFetches DDL / body for each"]
        RAW["Raw SQL Object Store\n.sql files per object\n(local / Blob / Git staging area)"]
    end

    subgraph CONVERT["Stage 2 — LLM Conversion"]
        PROMPT["Prompt Template\nTarget dialect instructions:\n• Convert T-SQL → PySpark / DLT SQL\n• Apply Delta Lake patterns\n• Preserve business logic\n• Flag unsupported constructs"]
        LLM["LLM\n(e.g. Claude / GPT)\nObject-by-object conversion"]
        OUT["Converted Output Store\nPySpark notebooks (.py)\nDelta Live Tables SQL (.sql)\nper-object output files"]
    end

    subgraph VALIDATE["Stage 3 — Validation"]
        REVIEW["Review & Validation\nSyntax check\nBusiness logic spot-check\nOptional: automated test run"]
        RETRY["Re-prompt Loop\n(if validation fails)\nAdjust prompt / fix issues\nre-submit to LLM"]
    end

    subgraph DEPLOY["Stage 4 — Deployment"]
        PUSH["Push to Databricks\n(Databricks Repos / Workspace API\nor Git integration)"]
    end

    subgraph TARGET["Target Platform — Databricks / Delta Lake"]
        NB["PySpark Notebooks\n(converted transformation logic)"]
        DLT["Delta Live Tables Pipelines\n(converted views & procedures)"]
        DELTA["Delta Lake\n(Bronze / Silver / Gold tables)"]
    end

    %% Source extraction
    SYN --> OBJS
    OBJS -->|"DDL / body extraction"| EXT
    EXT --> RAW

    %% LLM conversion
    RAW -->|"raw SQL object"| LLM
    PROMPT -->|"conversion instructions"| LLM
    LLM --> OUT

    %% Validation loop
    OUT --> REVIEW
    REVIEW -->|"pass"| PUSH
    REVIEW -->|"fail / issues flagged"| RETRY
    RETRY -->|"re-submit with revised prompt"| LLM

    %% Deployment
    PUSH --> NB
    PUSH --> DLT

    %% Target execution
    NB --> DELTA
    DLT --> DELTA
```

---

## Pipeline Summary

| Stage | Purpose | Key Tools |
|---|---|---|
| Extraction | Enumerate and export all SQL objects from source warehouse | Python, `pyodbc`, `INFORMATION_SCHEMA`, `sys.sql_modules` |
| LLM Conversion | Translate T-SQL logic to PySpark / DLT SQL using a structured prompt | LLM API (Claude / GPT), prompt engineering |
| Validation | Check syntax correctness and preserve business logic | Manual review, optional automated syntax check |
| Deployment | Push converted artefacts to Databricks target environment | Databricks REST API / Repos / Git |

## Design Notes
- Each SQL object is converted independently, keeping prompts focused and outputs manageable.
- The prompt template carries target-dialect rules (Delta Lake patterns, PySpark equivalents, unsupported construct flagging) as a reusable system instruction.
- The re-prompt loop handles cases where the LLM output requires correction before deployment.
- Output files are saved before deployment so conversions can be reviewed, versioned, and rerun without re-extracting from source.
