from elasticsearch import Elasticsearch
import pandas as pd

# -------------------
# CONNECT TO ELASTIC
# -------------------
es = Elasticsearch("http://localhost:9200")
INDEX = "nifty_data_weekly"

# -------------------
# QUERY 1 (Filtered)
# -------------------
query1 = {
    "track_total_hits": True,
    "size": 1000,
    "_source": ["ticker", "crossed_resistance", "close", "date"],
    "query": {
        "bool": {
            "must": [
                {"range": {"crossed_resistance.support_distance_pct": {"lte": 10}}},
                {"term": {"vcp_trend_template": True}},
                {"term": {"date": "2026-02-02"}}
            ]
        }
    }
}

res1 = es.search(index=INDEX, body=query1)
hits1 = res1["hits"]["hits"]

rows1 = []
date_value = None

for h in hits1:
    src = h["_source"]
    ticker = src["ticker"].replace(".NS", "")
    close = src.get("close")
    date_value = src.get("date")

    for cr in src.get("crossed_resistance", []):
        rows1.append({
            "Ticker": ticker,
            "Support": cr.get("support_level"),
            "Resistance": cr.get("resistance_level"),
            "Close": close
        })

df_matched = pd.DataFrame(rows1)

# -------------------
# QUERY 2 (Full Universe using captured date)
# -------------------
query2 = {
    "track_total_hits": True,
    "size": 1000,
    "_source": ["ticker", "crossed_resistance", "close"],
    "query": {
        "bool": {
            "must": [
                {"term": {"vcp_trend_template": True}},
                {"term": {"date": date_value}}
            ]
        }
    }
}

res2 = es.search(index=INDEX, body=query2)
hits2 = res2["hits"]["hits"]

rows2 = []

for h in hits2:
    src = h["_source"]
    ticker = src["ticker"].replace(".NS", "")
    close = src.get("close")

    for cr in src.get("crossed_resistance", []):
        rows2.append({
            "Ticker": ticker,
            "Support": cr.get("support_level"),
            "Resistance": cr.get("resistance_level"),
            "Close": close
        })

df_all = pd.DataFrame(rows2)

# -------------------
# FIND MISSED TICKERS
# -------------------
matched_tickers = set(df_matched["Ticker"])
df_missed = df_all[~df_all["Ticker"].isin(matched_tickers)]

# -------------------
# SAVE SINGLE EXCEL (2 SHEETS)
# -------------------
with pd.ExcelWriter("support_resistance_scan.xlsx") as writer:
    df_matched.to_excel(writer, sheet_name="matched", index=False)
    df_missed.to_excel(writer, sheet_name="missed", index=False)

print("✅ support_resistance_scan.xlsx created")
print(f"Matched tickers: {df_matched['Ticker'].nunique()}")
print(f"Missed tickers: {df_missed['Ticker'].nunique()}")
