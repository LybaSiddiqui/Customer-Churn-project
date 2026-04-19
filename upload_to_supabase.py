"""
upload_to_supabase.py

Run this ONCE to upload all 5 CSV files to your Supabase project.

Before running:
  1. Fill in your SUPABASE_URL and SUPABASE_KEY below
  2. Make sure the tables exist in Supabase (run migration.sql first)
  3. Run:  python upload_to_supabase.py
"""

import pandas as pd
from supabase import create_client

# ── fill these in ─────────────────────────────────────────────
SUPABASE_URL = "https://pyxgrvrqibfuhhrwmzav.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB5eGdydnJxaWJmdWhocndtemF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0Njk0MzcsImV4cCI6MjA5MjA0NTQzN30.elNyQ6ufol4kxsbyGE9EIvqYBsjzC4lBtw8EMr1O3jM"
# ─────────────────────────────────────────────────────────────

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def read_csv(filename):
    return pd.read_csv(
        filename,
        sep=";",
        quotechar='"',
        encoding="utf-8",
    )

def upload(table, df, chunk_size=500):
    """Upload a DataFrame to Supabase in chunks."""
    df = df.where(pd.notnull(df), None)  # replace NaN with None
    records = df.to_dict(orient="records")
    total = len(records)
    print(f"\n→ Uploading {total} rows to '{table}'...")
    for i in range(0, total, chunk_size):
        chunk = records[i:i+chunk_size]
        supabase.table(table).insert(chunk).execute()
        done = min(i + chunk_size, total)
        print(f"  {done}/{total}", end="\r")
    print(f"  ✅ {total} rows uploaded to '{table}'")


# ── 1. customers ──────────────────────────────────────────────
df = read_csv("customers.csv")
df.columns = ["customerid","firstname","lastname","age",
              "gender","email","phone","registrationdate"]
df["registrationdate"] = pd.to_datetime(df["registrationdate"]).dt.strftime("%Y-%m-%d")
upload("customers", df)

# ── 2. products ───────────────────────────────────────────────
df = read_csv("products.csv")
df.columns = ["productid","productname","category","price"]
upload("products", df)

# ── 3. transactions ───────────────────────────────────────────
df = read_csv("transactions.csv")
df.columns = ["transactionid","customerid","productid",
              "transactiondate","quantity","totalamount"]
df["transactiondate"] = pd.to_datetime(df["transactiondate"]).dt.strftime("%Y-%m-%d")
upload("transactions", df)

# ── 4. behavioral_metrics ─────────────────────────────────────
df = read_csv("behavioural.csv")
df.columns = ["customerid","purchasefrequency","averagespending","recencyofpurchase"]
upload("behavioral_metrics", df)

# ── 5. segmentation_results ───────────────────────────────────
df = read_csv("segmentation.csv")
df.columns = ["segmentationid","customerid","clusterid",
              "segmentlabel","segmentationdate"]
df["segmentationdate"] = pd.to_datetime(df["segmentationdate"]).dt.strftime("%Y-%m-%d")
upload("segmentation_results", df)

print("\n🎉 All tables uploaded successfully!")
