#!/usr/bin/env python3
"""
apiazurepre.py
"""

import os
import time
from typing import Dict, Any, Optional, Tuple

import requests
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

# -------------------------- Utilities --------------------------

def require_env(name: str) -> str:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v

def get_env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if not v:
        return default
    try:
        return int(v)
    except:
        return default

def get_env_float(name: str, default: float) -> float:
    v = os.getenv(name)
    if not v:
        return default
    try:
        return float(v)
    except:
        return default

def make_sqlalchemy_engine():
    enc = "yes" if os.getenv("SQL_ENCRYPT", "True").lower() == "true" else "no"
    trs = "yes" if os.getenv("SQL_TRUST", "True").lower() == "true" else "no"

    connection_url = URL.create(
        "mssql+pyodbc",
        username=require_env("SQL_USER"),
        password=require_env("SQL_PASS"),
        host=require_env("SQL_HOST"),
        database=require_env("SQL_DB"),
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "Encrypt": enc,
            "TrustServerCertificate": trs,
        },
    )
    return create_engine(connection_url, echo=False, pool_pre_ping=True)

def snowflake_connect():
    cfg = {
        "account": require_env("SF_ACCOUNT"),
        "user": require_env("SF_USER"),
        "password": require_env("SF_PASSWORD"),
        "database": require_env("SF_DB"),
        "schema": require_env("SF_SCHEMA"),
    }
    role = os.getenv("SF_ROLE"); wh = os.getenv("SF_WH")
    if role: cfg["role"] = role
    if wh: cfg["warehouse"] = wh
    return snowflake.connector.connect(**cfg)

# -------------------------- HTTP with retry --------------------------

def request_with_retry(url: str, params: Dict[str, Any], timeout: int, max_retries: int, backoff: float) -> Optional[requests.Response]:
    attempt = 0
    while True:
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code in (429, 500, 502, 503, 504):
                attempt += 1
                if attempt > max_retries:
                    print(f"[API] Max retries exceeded ({resp.status_code})")
                    return resp
                sleep_for = backoff * (2 ** (attempt - 1))
                print(f"[API] Retry {attempt}/{max_retries} in {sleep_for:.2f}s")
                time.sleep(sleep_for)
            else:
                return resp
        except requests.exceptions.RequestException as e:
            attempt += 1
            if attempt > max_retries:
                print(f"[API] Final exception: {e}")
                return None
            sleep_for = backoff * (2 ** (attempt - 1))
            print(f"[API] Exception: {e}, retrying in {sleep_for:.2f}s")
            time.sleep(sleep_for)

# -------------------------- Geoapify helpers --------------------------
# (UPDATED WITH ALFIE’S NEW LOGIC)
# ----------------------------------------------------------------------

def retrieve_address_data(lat: str, lon: str, api_key: str, timeout: int, max_retries: int, backoff: float) -> pd.DataFrame:
    url = "https://api.geoapify.com/v1/geocode/reverse"
    params = {"lat": lat, "lon": lon, "apiKey": api_key, "format": "json"}

    resp = request_with_retry(url, params, timeout, max_retries, backoff)
    if resp is None or resp.status_code != 200:
        return pd.DataFrame()

    data = resp.json()
    results = data.get("results", [])
    if not results:
        return pd.DataFrame()

    rec = results[0]
    wanted = ["name", "housenumber", "street", "suburb", "city", "state", "postcode", "country"]
    row = [rec.get(k) for k in wanted]

    return pd.DataFrame([row], columns=wanted)

def other_details(lat: str, lon: str, api_key: str, timeout: int, max_retries: int, backoff: float) -> pd.DataFrame:
    url = "https://api.geoapify.com/v2/place-details"
    params = {
        "lat": lat, "lon": lon, "apiKey": api_key,
        "format": "json", "features": ["building.places"]
    }

    resp = request_with_retry(url, params, timeout, max_retries, backoff)
    if resp is None or resp.status_code != 200:
        return pd.DataFrame([["None", "None", "None", "None"]],
                            columns=["phone", "website", "opening_hours", "wheelchair"])

    data = resp.json()
    feats = data.get("features", [])
    if not feats:
        return pd.DataFrame([["None", "None", "None", "None"]],
                            columns=["phone", "website", "opening_hours", "wheelchair"])

    try:
        raw = feats[0]["properties"]["datasource"]["raw"]
        wanted = ["phone", "website", "opening_hours", "wheelchair"]
        row = [raw.get(k) for k in wanted]
        return pd.DataFrame([row], columns=wanted)
    except:
        return pd.DataFrame([["None", "None", "None", "None"]],
                            columns=["phone", "website", "opening_hours", "wheelchair"])

def construct_address(lat: str, lon: str, api_key: str, timeout: int, max_retries: int, backoff: float) -> Tuple:
    df = retrieve_address_data(lat, lon, api_key, timeout, max_retries, backoff)
    if df.empty:
        return 0

    try:
        restaurant_name = df.iloc[0]["name"] or ""
        num = df.iloc[0]["housenumber"] or ""
        street = df.iloc[0]["street"] or ""
        suburb = df.iloc[0]["suburb"] or ""
        city = df.iloc[0]["city"] or ""
        zip_code = df.iloc[0]["postcode"] or ""
        country = df.iloc[0]["country"] or ""

        if city == "New York":
            city = "Ny"

        address = f"{num} {street}, {suburb}".strip().strip(",")

        return address, restaurant_name, zip_code, suburb, city, street, country

    except Exception as e:
        print("[Address] Error:", e)
        return 0


# -------------------------- SQL Reader --------------------------

def load_source_from_sql() -> pd.DataFrame:
    engine = make_sqlalchemy_engine()

    custom_query = os.getenv("SQL_SRC_QUERY")
    table = os.getenv("SQL_SRC_TABLE", "SCHEMA.RESTURAT_TABLE")

    if custom_query:
        sql = custom_query
    else:
        sql = f"""
            SELECT
              restaurant_id AS RESTAURANT_ID,
              latitude AS LATITUDE,
              longitude AS LONGITUDE
            FROM {table}
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        """

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)

    df = df.dropna(subset=["LATITUDE", "LONGITUDE"]).reset_index(drop=True)
    return df

# -------------------------- MAIN --------------------------

def main():
    api_key = require_env("GEO_API_KEY")
    target_table = os.getenv("TARGET_TABLE", "RESTAURANT_API_RESULTS")

    api_timeout = get_env_int("API_TIMEOUT", 30)
    api_max_retries = get_env_int("API_MAX_RETRIES", 3)
    api_backoff = get_env_float("API_BACKOFF_SECS", 1.0)

    df_src = load_source_from_sql()
    if df_src.empty:
        print("[WARN] No rows found.")
        return

    out_cols = [
        "RESTAURANT_ID", "RESTAURANT_NAME", "ADDRESS",
        "ZIP_CODE", "SUBURB", "CITY", "STREET", "COUNTRY",
        "PHONE", "WEBSITE", "HOURS", "WHEELCHAIR"
    ]
    out = {c: [] for c in out_cols}

    for _, row in df_src.iterrows():
        rid = row["RESTAURANT_ID"]
        lat, lon = str(row["LATITUDE"]), str(row["LONGITUDE"])

        addr = construct_address(lat, lon, api_key, api_timeout, api_max_retries, api_backoff)
        if addr == 0:
            out["ADDRESS"].append("incorrect address")
            out["RESTAURANT_NAME"].append("no address found")
            out["ZIP_CODE"].append(None)
            out["SUBURB"].append(None)
            out["CITY"].append(None)
            out["STREET"].append(None)
            out["COUNTRY"].append(None)
        else:
            out["ADDRESS"].append(addr[0])
            out["RESTAURANT_NAME"].append(addr[1])
            out["ZIP_CODE"].append(addr[2])
            out["SUBURB"].append(addr[3])
            out["CITY"].append(addr[4])
            out["STREET"].append(addr[5])
            out["COUNTRY"].append(addr[6])

        det = other_details(lat, lon, api_key, api_timeout, api_max_retries, api_backoff)
        out["PHONE"].append(str(det.iloc[0]["phone"]))
        out["WEBSITE"].append(str(det.iloc[0]["website"]))
        out["HOURS"].append(str(det.iloc[0]["opening_hours"]))
        out["WHEELCHAIR"].append(str(det.iloc[0]["wheelchair"]))

        out["RESTAURANT_ID"].append(rid)

    df_out = pd.DataFrame(out)

    conn = snowflake_connect()
    try:
        ok, _, nrows, _ = write_pandas(
            conn,
            df_out,
            table_name=target_table,
            database=require_env("SF_DB"),
            schema=require_env("SF_SCHEMA"),
            auto_create_table=True,
            overwrite=True,
        )
        print(f"[SF] Wrote {nrows} rows.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()