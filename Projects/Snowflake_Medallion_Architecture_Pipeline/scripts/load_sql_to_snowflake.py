import os
import re
import csv
import json
import shutil
import threading
from queue import Queue
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import snowflake.connector

# -----------------------------------------------------------------------------
# CONFIG FROM ENVIRONMENT VARIABLES
# -----------------------------------------------------------------------------
sql_host   = os.environ["SQL_HOST"]
sql_db     = os.environ["SQL_DB"]
sql_user   = os.environ["SQL_USER"]
sql_pass   = os.environ["SQL_PASS"]
sql_encrypt= os.environ.get("SQL_ENCRYPT", "True")
sql_trust  = os.environ.get("SQL_TRUST", "True")

table_map = pd.DataFrame(json.loads(os.environ["TABLE_MAP"]))

sf_acct    = os.environ["SF_ACCOUNT"]
sf_user    = os.environ["SF_USER"]
sf_pass    = os.environ["SF_PASSWORD"]
sf_role    = os.environ["SF_ROLE"]
sf_wh      = os.environ["SF_WH"]
sf_db      = os.environ["SF_DB"]
sf_schema  = os.environ["SF_SCHEMA"]
sf_kind    = os.environ.get("SF_TABLE_KIND", "TRANSIENT").upper()

status_tbl = os.environ.get("STATUS_FLAGS_TABLE", "STATUS_FLAGS")

# Working directory (auto-cleaned)
tmp_root = Path(os.environ.get("Agent_TempDirectory", ".")) / "csv_loads"
tmp_root.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# SQL Server Engine
# -----------------------------------------------------------------------------
connection_url = URL.create(
    "mssql+pyodbc",
    username=sql_user,
    password=sql_pass,
    host=sql_host,
    database=sql_db,
    query={
        "driver": "ODBC Driver 18 for SQL Server",
        "TrustServerCertificate": "yes" if sql_trust.lower() == "true" else "no",
        "Encrypt": "yes" if sql_encrypt.lower() == "true" else "no",
    },
)

sql_engine = create_engine(connection_url, echo=False, pool_pre_ping=True)


# -----------------------------------------------------------------------------
# Snowflake Connection
# -----------------------------------------------------------------------------
sf_conn = snowflake.connector.connect(
    account=sf_acct,
    user=sf_user,
    password=sf_pass,
    role=sf_role,
    warehouse=sf_wh,
    database=sf_db,
    schema=sf_schema,
)
sf_cur = sf_conn.cursor()
sf_cur.execute(f"ALTER WAREHOUSE {sf_wh} RESUME IF SUSPENDED")


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def norm(s: str) -> str:
    s = s.strip().strip('"').strip("'")
    s = re.sub(r"[^A-Za-z0-9_]", "_", s)
    if s and s[0].isdigit():
        s = "_" + s
    return s.upper()


def get_schema(src):
    schema, table = src.split(".", 1)
    q = f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,
               NUMERIC_PRECISION, NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='{schema}'
          AND TABLE_NAME='{table}'
        ORDER BY ORDINAL_POSITION
    """
    with sql_engine.connect() as conn:
        return pd.read_sql(q, conn)


def map_type(r):
    dt = str(r["DATA_TYPE"]).lower()
    length = r["CHARACTER_MAXIMUM_LENGTH"]
    prec = r["NUMERIC_PRECISION"]
    scale = r["NUMERIC_SCALE"]

    if dt in ("int", "integer"): return "INTEGER"
    if dt == "bigint": return "BIGINT"
    if dt in ("smallint", "tinyint"): return "INTEGER"
    if dt == "bit": return "BOOLEAN"
    if dt in ("decimal", "numeric", "money", "smallmoney"):
        if pd.notna(prec) and pd.notna(scale):
            return f"NUMBER({int(prec)},{int(scale)})"
        return "NUMBER"
    if dt in ("float", "real"): return "FLOAT"
    if dt in ("datetime", "datetime2", "smalldatetime", "timestamp"):
        return "TIMESTAMP_NTZ"
    if dt == "date": return "DATE"
    if dt == "time": return "TIME"
    if dt in ("varchar", "char", "text", "nchar", "nvarchar", "ntext"):
        if pd.notna(length) and 0 < int(length) < 16777216:
            return f"VARCHAR({int(length)})"
        return "VARCHAR"
    if dt in ("binary", "varbinary", "image"): return "BINARY"
    if dt == "uniqueidentifier": return "VARCHAR(36)"
    return "VARCHAR"


def recreate_table(src, dst):
    schema_df = get_schema(src)
    cols = []
    ddl = []

    for _, r in schema_df.iterrows():
        c = norm(r["COLUMN_NAME"])
        cols.append(c)
        ddl.append(f"{c} {map_type(r)}")

    dst_norm = norm(dst)
    full_dst = f"{sf_db}.{sf_schema}.{dst_norm}"

    kind = "TRANSIENT" if sf_kind == "TRANSIENT" else "TEMPORARY"
    sf_cur.execute(f"CREATE OR REPLACE {kind} TABLE {full_dst} ({', '.join(ddl)})")

    return full_dst, cols


# -----------------------------------------------------------------------------
# Extraction Logic (Chunked)
# -----------------------------------------------------------------------------
def extract_to_csv(src, dst, approx_rows):
    # Automatic chunk size based on table size
    if approx_rows > 2_000_000:
        chunk = 200_000  # customers
    elif approx_rows > 700_000:
        chunk = 150_000  # riders
    else:
        chunk = 100_000  # restaurants

    print(f"[Extract] {src} using chunks of {chunk} rows")

    dst_norm = norm(dst)
    table_dir = tmp_root / dst_norm
    if table_dir.exists():
        shutil.rmtree(table_dir)
    table_dir.mkdir(parents=True)

    sql = f"SELECT * FROM {src}"
    file_paths = []
    idx = 0
    total = 0

    with sql_engine.connect() as conn:
        for df in pd.read_sql(sql, conn, chunksize=chunk):
            if df.empty:
                continue
            df.columns = [norm(c) for c in df.columns]

            idx += 1
            out = table_dir / f"{dst_norm}_{idx:05d}.csv"
            df.to_csv(out, index=False, quoting=csv.QUOTE_MINIMAL)
            file_paths.append(out)
            total += len(df)

    print(f"[Extract OK] {src}: {total} rows into {len(file_paths)} files")
    return table_dir, file_paths


# -----------------------------------------------------------------------------
# Multi-threaded PUT uploader
# -----------------------------------------------------------------------------
def uploader_worker(q, stage):
    while True:
        path = q.get()
        if path is None:
            break
        uri = f"file://{path.as_posix()}"
        sf_cur.execute(
            f"PUT '{uri}' @{stage} AUTO_COMPRESS=TRUE PARALLEL=8 OVERWRITE=TRUE"
        )
        q.task_done()


def parallel_put(files, stage, workers=4):
    q = Queue()
    threads = []

    for _ in range(workers):
        t = threading.Thread(target=uploader_worker, args=(q, stage))
        t.start()
        threads.append(t)

    for f in files:
        q.put(f)

    q.join()

    for _ in range(workers):
        q.put(None)
    for t in threads:
        t.join()


# -----------------------------------------------------------------------------
# COPY INTO
# -----------------------------------------------------------------------------
def copy_into(full_dst, cols, stage):
    col_list = ", ".join(cols)
    sf_cur.execute(f"""
        COPY INTO {full_dst} ({col_list})
        FROM @{stage}
        FILE_FORMAT = {sf_db}.{sf_schema}.CSV_AUTO_GZ
        PURGE=TRUE
        ON_ERROR=CONTINUE
    """)


# -----------------------------------------------------------------------------
# Main Pipeline
# -----------------------------------------------------------------------------
sf_cur.execute(f"""
    CREATE OR REPLACE FILE FORMAT {sf_db}.{sf_schema}.CSV_AUTO_GZ
      TYPE=CSV
      FIELD_DELIMITER=','
      SKIP_HEADER=1
      FIELD_OPTIONALLY_ENCLOSED_BY='\"'
      NULL_IF=('','NULL','null')
      EMPTY_FIELD_AS_NULL=TRUE
      COMPRESSION=AUTO
""")

for _, row in table_map.iterrows():
    src = row["src"]
    dst = row["dst"]

    # determine approximate sizes
    if "customer" in src.lower():
        approx = 3_000_000
    elif "rider" in src.lower():
        approx = 1_000_000
    else:
        approx = 350_000

    print(f"\n====== Loading {src} -> {dst} ======")

    # 1) Recreate table
    full_dst, cols = recreate_table(src, dst)

    # 2) Extract chunks
    table_dir, files = extract_to_csv(src, dst, approx)

    # 3) Upload
    stage = f"~/{norm(dst)}"
    parallel_put(files, stage)

    # 4) COPY
    copy_into(full_dst, cols, stage)

    # Clean local temp
    shutil.rmtree(table_dir, ignore_errors=True)

    print(f"[OK] Loaded table {dst}")

# -----------------------------------------------------------------------------
# Final Snowflake Flag Update
# -----------------------------------------------------------------------------
try:
    sf_cur.execute(f"USE DATABASE {sf_db}")
    sf_cur.execute(f"USE SCHEMA {sf_schema}")
    sf_cur.execute(f"UPDATE {status_tbl} SET datainflag = 1")
    print("[OK] Status flag updated")
except Exception as e:
    print(f"[WARN] Could not update status flag: {e}")

print("\n[SUCCESS] All tables loaded successfully.")

sf_cur.close()
sf_conn.close()
sql_engine.dispose()
shutil.rmtree(tmp_root, ignore_errors=True)