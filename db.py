import streamlit as st
import pandas as pd
from supabase import create_client

@st.cache_resource
def get_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

def run_query(sql: str) -> tuple[pd.DataFrame, str | None]:
    try:
        client = get_client()
        clean  = sql.strip().rstrip(";")
        resp   = client.rpc("exec_sql", {"query": clean}).execute()
        data   = resp.data if resp and hasattr(resp, "data") else []
        return (pd.DataFrame(data), None) if data else (pd.DataFrame(), None)
    except Exception as e:
        return None, str(e)

def q(sql: str) -> pd.DataFrame:
    df, _ = run_query(sql)
    return df if df is not None else pd.DataFrame()

def insert(table: str, record: dict) -> tuple[bool, str]:
    try:
        get_client().table(table).insert(record).execute()
        return True, ""
    except Exception as e:
        return False, str(e)

def check_connected() -> bool:
    try:
        get_client().table("customers").select("customerid", count="exact").limit(1).execute()
        return True
    except:
        return False