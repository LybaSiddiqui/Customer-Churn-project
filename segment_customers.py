"""
segment_customers.py

Runs proper K-Means clustering on RFM features from behavioral_metrics,
then uploads the real segmentation results back to Supabase.

Install deps first:
    pip install supabase pandas scikit-learn

Then run:
    python segment_customers.py
"""

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from supabase import create_client
import warnings
warnings.filterwarnings("ignore")
try:
    import tomllib
except ImportError:
    import tomli as tomllib

# ── fill these in ─────────────────────────────────────────────
import tomllib
import os

# read from .streamlit/secrets.toml
secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
with open(secrets_path, "rb") as f:
    secrets = tomllib.load(f)

SUPABASE_URL = secrets["supabase"]["url"]
SUPABASE_KEY = secrets["supabase"]["key"]
N_CLUSTERS   = 6
# ─────────────────────────────────────────────────────────────

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("1. Fetching behavioral metrics from Supabase…")
resp = supabase.table("behavioral_metrics").select("*").execute()
df   = pd.DataFrame(resp.data)
print(f"   {len(df)} customers loaded")

# ── clean: drop inactive customers (0 purchases) ─────────────
df = df[df["purchasefrequency"] > 0].copy()
df["averagespending"]   = pd.to_numeric(df["averagespending"])
df["purchasefrequency"] = pd.to_numeric(df["purchasefrequency"])
df["recencyofpurchase"] = pd.to_numeric(df["recencyofpurchase"])
print(f"   {len(df)} active customers (removed 0-purchase rows)")

# ── RFM feature matrix ────────────────────────────────────────
# Recency:   lower = better (bought recently)
# Frequency: higher = better (buys often)
# Monetary:  higher = better (spends more)
X = df[["recencyofpurchase","purchasefrequency","averagespending"]].values

# ── scale features so K-Means isn't biased by magnitude ──────
scaler   = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ── K-Means clustering ────────────────────────────────────────
print(f"\n2. Running K-Means with {N_CLUSTERS} clusters…")
kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(X_scaled)

# ── label clusters by RFM quality ────────────────────────────
# Score each cluster: low recency + high freq + high spend = best
cluster_summary = df.groupby("cluster").agg(
    avg_recency   =("recencyofpurchase","mean"),
    avg_frequency =("purchasefrequency","mean"),
    avg_spend     =("averagespending","mean"),
    count         =("customerid","count"),
).reset_index()

# Composite score: lower recency = better, so invert it
cluster_summary["score"] = (
    - cluster_summary["avg_recency"]        # lower recency = better
    + cluster_summary["avg_frequency"] * 50 # weight frequency
    + cluster_summary["avg_spend"] * 0.1    # weight spend
)
cluster_summary = cluster_summary.sort_values("score", ascending=False).reset_index(drop=True)

# assign labels from best to worst
LABELS = [
    "VIP Loyalists",
    "High Value",
    "Regular Customers",
    "Medium Value",
    "At Risk",
    "Dormant / No Purchases",
]
label_map = {
    row["cluster"]: LABELS[i]
    for i, row in cluster_summary.iterrows()
}
cluster_id_map = {
    row["cluster"]: i + 1
    for i, row in cluster_summary.iterrows()
}

df["segmentlabel"] = df["cluster"].map(label_map)
df["clusterid"]    = df["cluster"].map(cluster_id_map)

# ── print summary ─────────────────────────────────────────────
print("\n3. Cluster summary:")
print("-" * 70)
for i, row in cluster_summary.iterrows():
    lbl = LABELS[i]
    print(f"  {lbl:<30} | {int(row['count']):>5} customers "
          f"| Recency {row['avg_recency']:.0f}d "
          f"| Freq {row['avg_frequency']:.1f}x "
          f"| Spend ${row['avg_spend']:.0f}")
print("-" * 70)

# ── build segmentation rows ───────────────────────────────────
from datetime import date
today = date.today().isoformat()

records = [
    {
        "customerid":       int(row["customerid"]),
        "clusterid":        int(row["clusterid"]),
        "segmentlabel":     row["segmentlabel"],
        "segmentationdate": today,
    }
    for _, row in df.iterrows()
]

# also add dormant customers (0 purchases) as "Dormant / No Purchases"
resp2   = supabase.table("behavioral_metrics").select("customerid").eq("purchasefrequency", 0).execute()
dormant = pd.DataFrame(resp2.data)
if not dormant.empty:
    dormant_records = [
        {
            "customerid":       int(r["customerid"]),
            "clusterid":        N_CLUSTERS,
            "segmentlabel":     "Dormant / No Purchases",
            "segmentationdate": today,
        }
        for _, r in dormant.iterrows()
    ]
    records.extend(dormant_records)
    print(f"\n   Added {len(dormant)} dormant customers")

# ── upload to Supabase ────────────────────────────────────────
print(f"\n4. Uploading {len(records)} segmentation records to Supabase…")

# clear old segmentation first
supabase.table("segmentation_results").delete().neq("segmentationid", 0).execute()
print("   Old segmentation cleared")

chunk_size = 500
for i in range(0, len(records), chunk_size):
    chunk = records[i:i+chunk_size]
    supabase.table("segmentation_results").insert(chunk).execute()
    print(f"   {min(i+chunk_size, len(records))}/{len(records)}", end="\r")

print(f"\n\n✅ Done! {len(records)} customers segmented and uploaded.")
print("\nNew segment distribution:")
dist = df.groupby("segmentlabel")["customerid"].count().sort_values(ascending=False)
for label, count in dist.items():
    print(f"  {label:<30} {count:>5}")