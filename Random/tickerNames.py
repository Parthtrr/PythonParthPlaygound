import requests
import pandas as pd
import io
import yfinance as yf
from datetime import datetime, timedelta
from typing import List

def get_nifty500_yf_tickers() -> List[str]:
    """
    Fetch NIFTY 500 components reliably from niftyindices.com,
    then return Yahoo Finance-compatible tickers (e.g. RELIANCE.NS).
    """
    url = "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv"
    base_url = "https://www.niftyindices.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": base_url,
        "Connection": "keep-alive"
    }

    session = requests.Session()
    session.get(base_url, headers=headers)
    resp = session.get(url, headers=headers)
    resp.raise_for_status()

    df = pd.read_csv(io.StringIO(resp.text))
    if "Symbol" not in df.columns:
        raise ValueError(f"Unexpected CSV columns: {df.columns.tolist()}")

    symbols = df["Symbol"].str.strip().tolist()
    yf_symbols = [f"{s}.NS" for s in symbols]
    return yf_symbols


def test_yfinance_tickers(tickers: List[str]) -> pd.DataFrame:
    """
    Tests each ticker by fetching last week's daily data.
    Returns DataFrame with columns [Ticker, Status, Error].
    """
    start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    end = datetime.now().strftime("%Y-%m-%d")

    results = []
    for t in tickers:
        try:
            df = yf.download(t, start=start, end=end, interval="1d", progress=False)
            if df is None or df.empty:
                results.append({"Ticker": t, "Status": "FAIL", "Error": "Empty/Null data"})
                print(f"❌ {t} -> Empty or null data")
            else:
                results.append({"Ticker": t, "Status": "SUCCESS", "Error": ""})
        except Exception as e:
            results.append({"Ticker": t, "Status": "FAIL", "Error": str(e)})
            print(f"❌ {t} -> {e}")
    return pd.DataFrame(results)


if __name__ == "__main__":
    print("Fetching NIFTY 500 tickers ...")
    tickers = get_nifty500_yf_tickers()
    print(f"✅ Total tickers fetched: {len(tickers)}")

    print("\nTesting tickers via yfinance (1-week daily data)...\n")
    df_results = test_yfinance_tickers(tickers)

    success_df = df_results[df_results["Status"] == "SUCCESS"]
    fail_df = df_results[df_results["Status"] == "FAIL"]

    print(f"\n✅ Successful tickers: {len(success_df)}")
    print(f"❌ Failed tickers: {len(fail_df)}")

    # Save curated successful list to Excel
    output_file = "nifty500_valid_tickers.xlsx"
    success_df[["Ticker"]].to_excel(output_file, index=False)
    print(f"\n📁 Curated tickers saved to: {output_file}")

    # Optional: also save full test log
    df_results.to_excel("nifty500_ticker_test_log.xlsx", index=False)
