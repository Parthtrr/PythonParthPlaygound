from elasticsearch import Elasticsearch
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================================
# CONFIG
# ==========================================================
ES_HOST = "http://localhost:9200"
TECH_INDEX = "nifty_data_weekly"
FUND_INDEX = "nifty_fundamental"
SCAN_DATE = "2026-02-09"

OUTPUT_FILE = "support_resistance_scan.xlsx"

es = Elasticsearch(ES_HOST)

# ==========================================================
# STATIC DATA — INDICES
# ==========================================================

df_indices = pd.DataFrame({
    "Index Name": [
        "USDINR", "XAUINRG", "XAGINRK", "NASDAQ 100",
        "NIFTY 50", "NIFTY 500", "NIFTY MIDCAP 150",
        "NIFTY SMALLCAP 250", "NIFTY BANK",
        "NIFTY PRIVATE BANK", "NIFTY PSU BANK",
        "NIFTY FINANCIAL SERVICES", "NIFTY FMCG",
        "NIFTY IT", "NIFTY AUTO", "NIFTY METAL",
        "NIFTY PHARMA", "NIFTY HEALTHCARE",
        "NIFTY REALTY", "NIFTY MEDIA",
        "NIFTY CONSUMER DURABLES", "NIFTY OIL & GAS",
        "NIFTY CHEMICAL", "NIFTY DEFENCE",
        "NIFTY DIGITAL INDIA", "NIFTY EV",
        "NIfty Energy"
    ],
    "STATUS": ["" for _ in range(27)]
})

# ==========================================================
# STATIC DATA — MUTUAL FUND
# ==========================================================

df_mf = pd.DataFrame({
    "Indices": [
        "NIFTY 50",
        "NIFTY Mid cap 150",
        "NIFTY Small cap 250",
        "NIFTY Financial Services",
        "NIFTY India Digital",
        "NIFTY India Healthcare"
    ],
    "Benchmark RSI": [40, 39.41, 38.69, 41, 39, 37.27],
    "Current RSI": [53.26, 52.89, 42.02, 58.19, 39.91, 43.73],
    "Mutual fund to invest": [
        "Parag Parikh Flexi Cap Fund Direct Growth",
        "HDFC Mid Cap Fund Direct Growth",
        "Nippon India Small Cap Fund direct growth",
        "SBI Banking & Financial Services Fund",
        "Tata Digital India Fund",
        "ICICI Prudential Pharma Healthcare & Diagnostics Fund"
    ]
})

# ==========================================================
# UTILITY FUNCTIONS
# ==========================================================

def calculate_growth(current, previous):
    if previous in [0, None]:
        return np.nan
    return round(((current - previous) / previous) * 100, 2)


def calculate_slope(values):
    if len(values) < 5:
        return np.nan
    x = np.arange(len(values))
    slope = np.polyfit(x, values, 1)[0]
    return round(slope, 2)


# ==========================================================
# NET SCORE FUNCTION
# ==========================================================

def calculate_net_score(row):

    score = 0

    score += 1 if row["Sales_QoQ_%"] > 0 else -1
    score += 1 if row["Profit_QoQ_%"] > 0 else -1
    score += 1 if row["EPS_QoQ_%"] > 0 else -1

    score += 2 if row["Sales_YoY_%"] > 0 else -2
    score += 2 if row["Profit_YoY_%"] > 0 else -2
    score += 2 if row["EPS_YoY_%"] > 0 else -2

    score += 3 if row["Sales_Slope_5Q"] > 0 else -3
    score += 3 if row["Profit_Slope_5Q"] > 0 else -3

    return score


# ==========================================================
# TECHNICAL SCAN
# ==========================================================

def fetch_matched_and_all():

    query1 = {
        "track_total_hits": True,
        "size": 1000,
        "_source": ["ticker", "crossed_resistance", "close", "date"],
        "query": {
            "bool": {
                "must": [
                    {"range": {"crossed_resistance.support_distance_pct": {"lte": 10}}},
                    {"term": {"vcp_trend_template": True}},
                    {"term": {"date": SCAN_DATE}}
                ]
            }
        }
    }

    res1 = es.search(index=TECH_INDEX, body=query1)
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

    res2 = es.search(index=TECH_INDEX, body=query2)
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

    matched_tickers = set(df_matched["Ticker"])
    df_missed = df_all[~df_all["Ticker"].isin(matched_tickers)]

    return df_matched, df_missed


# ==========================================================
# FUNDAMENTAL ENRICHMENT
# ==========================================================

def get_fundamental_data(ticker):

    empty_result = {
        "Sector": np.nan,
        "Industry": np.nan,
        "Sales_QoQ_%": 0,
        "Profit_QoQ_%": 0,
        "EPS_QoQ_%": 0,
        "Sales_YoY_%": 0,
        "Profit_YoY_%": 0,
        "EPS_YoY_%": 0,
        "Sales_Slope_5Q": 0,
        "Profit_Slope_5Q": 0
    }

    try:
        res = es.get(index=FUND_INDEX, id=ticker)
        src = res["_source"]

        sector = src.get("sector", {}).get("sector")
        industry = src.get("sector", {}).get("industry")

        quarterly = src.get("quarterly", [])

        sales, profits, eps = [], [], []

        for q in quarterly:
            if q["metric"] == "Sales":
                sales.append((q["period_date"], q["value"]))
            elif q["metric"] == "Net Profit":
                profits.append((q["period_date"], q["value"]))
            elif q["metric"] == "EPS in Rs":
                eps.append((q["period_date"], q["value"]))

        sales = sorted(sales)
        profits = sorted(profits)
        eps = sorted(eps)

        if len(sales) < 5 or len(profits) < 5 or len(eps) < 5:
            empty_result["Sector"] = sector
            empty_result["Industry"] = industry
            return empty_result

        sales_vals = [v for _, v in sales][-5:]
        profit_vals = [v for _, v in profits][-5:]
        eps_vals = [v for _, v in eps][-5:]

        return {
            "Sector": sector,
            "Industry": industry,
            "Sales_QoQ_%": calculate_growth(sales_vals[-1], sales_vals[-2]),
            "Profit_QoQ_%": calculate_growth(profit_vals[-1], profit_vals[-2]),
            "EPS_QoQ_%": calculate_growth(eps_vals[-1], eps_vals[-2]),
            "Sales_YoY_%": calculate_growth(sales_vals[-1], sales_vals[0]),
            "Profit_YoY_%": calculate_growth(profit_vals[-1], profit_vals[0]),
            "EPS_YoY_%": calculate_growth(eps_vals[-1], eps_vals[0]),
            "Sales_Slope_5Q": calculate_slope(sales_vals),
            "Profit_Slope_5Q": calculate_slope(profit_vals)
        }

    except Exception:
        return empty_result


def enrich_dataframe(df):

    unique_tickers = df["Ticker"].unique()
    fundamentals = []

    for ticker in unique_tickers:
        data = get_fundamental_data(ticker)
        data["Ticker"] = ticker
        fundamentals.append(data)

    fund_df = pd.DataFrame(fundamentals)

    df = df.merge(fund_df, on="Ticker", how="left")

    df["Net_Score"] = df.apply(calculate_net_score, axis=1)

    df = df.sort_values(by="Net_Score", ascending=False)

    return df


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    print("🔎 Running technical scan...")
    df_matched, df_missed = fetch_matched_and_all()

    print("📊 Enriching with fundamentals...")
    df_matched = enrich_dataframe(df_matched)
    df_missed = enrich_dataframe(df_missed)

    print("💾 Saving final Excel...")

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df_indices.to_excel(writer, sheet_name="indices", index=False)
        df_mf.to_excel(writer, sheet_name="MF", index=False)
        df_matched.to_excel(writer, sheet_name="matched", index=False)
        df_missed.to_excel(writer, sheet_name="missed", index=False)

    print("✅ Done!")
