import json
import re
import time
import pandas as pd
import yfinance as yf
from datetime import datetime
from serpapi import GoogleSearch

# ------------------ CONFIG ------------------
INPUT_FILE = "nifty_indices_yf_tradingview.xlsx"
OUTPUT_FILE = "nifty_indices_yf_tradingview_fixed_final.xlsx"
API_KEY = "df090ccf3e33c64c0a5b99495650dce9b1ae1a2180685330aa305f477bf82784"  # ← Replace with your actual SerpApi key
# --------------------------------------------


def log(msg, level="INFO"):
    """Simple console logger with timestamp and level."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def extract_ticker(link: str, title: str):
    """Extract Yahoo Finance ticker symbol from URL or title."""
    # Handle cases like https://finance.yahoo.com/quote/%5ENSEI/
    m = re.search(r'/quote/([A-Za-z0-9_^=.%+-]+)/?', link)
    if m:
        raw_ticker = m.group(1)
        ticker = raw_ticker.replace("%5E", "^")  # decode %5E
        return ticker

    # Fallback: try to extract from title like "NIFTY 50 (^NSEI)"
    m = re.search(r'\(([A-Z0-9^=.-]+)\)', title)
    if m:
        return m.group(1)

    return None


def fetch_ticker_from_google(index_name):
    """Search Yahoo Finance ticker using SerpApi."""
    query = f"{index_name} yahoo finance site:finance.yahoo.com"
    params = {
        "q": query,
        "hl": "en",
        "api_key": API_KEY
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])
        log(f"🔍 Searching for '{index_name}' — found {len(organic_results)} results")

        for r in organic_results:
            link = r.get("link", "")
            title = r.get("title", "")
            ticker = extract_ticker(link, title)

            if ticker:
                # Only pick NSE-related or index tickers (heuristic)
                if ticker.endswith(".NS") or ticker.startswith("^"):
                    log(f"✅ Found ticker '{ticker}' for '{index_name}'")
                    return ticker

        log(f"⚠️ No valid NSE ticker found for '{index_name}'", "WARN")
        return None

    except Exception as e:
        log(f"❌ Error fetching '{index_name}': {e}", "ERROR")
        return None


def validate_ticker(ticker):
    """Check if ticker works on yfinance."""
    try:
        df_yf = yf.download(ticker, period="5d", interval="1d", progress=False)
        if not df_yf.empty:
            log(f"✅ Ticker '{ticker}' validation SUCCESS (data found)")
            return "SUCCESS"
        else:
            log(f"⚠️ Ticker '{ticker}' validation FAILED (no data returned)", "WARN")
            return "FAIL"
    except Exception as e:
        log(f"❌ Error validating ticker '{ticker}': {e}", "ERROR")
        return "FAIL"


def main():
    log("🚀 Starting TradingView Ticker Fixer")
    log(f"Reading input file: {INPUT_FILE}")

    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        log(f"❌ Failed to read Excel file '{INPUT_FILE}': {e}", "ERROR")
        return

    new_rows = []

    for idx, row in df.iterrows():
        index_name = row["IndexName"]
        prev_status = str(row.get("Status", "FAIL"))
        prev_ticker = str(row.get("YFTicker", ""))

        log(f"\n➡️ Processing {idx+1}/{len(df)}: {index_name}")

        ticker = fetch_ticker_from_google(index_name)
        if ticker:
            status = validate_ticker(ticker)
        else:
            ticker, status = prev_ticker, "FAIL"
            log(f"❌ Not found for '{index_name}'", "WARN")

        new_rows.append((index_name, ticker, status))
        time.sleep(1)  # avoid rate limits

    df_out = pd.DataFrame(new_rows, columns=["IndexName", "YFTicker", "Status"])
    df_out.to_excel(OUTPUT_FILE, index=False)
    log(f"\n✅ Updated Excel saved → {OUTPUT_FILE}")
    log("🎉 Completed all tasks successfully!")


if __name__ == "__main__":
    main()
