import requests
from bs4 import BeautifulSoup
import pandas as pd
import time


def get_indices_from_screener(symbol: str):
    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # --- Extract Indices ---
        indices = []
        indices_block = soup.find("p", {"id": "benchmarks"})
        if indices_block:
            for a in indices_block.find_all("a"):
                text = a.get_text(strip=True)
                if text and text not in indices:
                    indices.append(text)

        # --- Extract Sector / Peer Info ---
        sector_info = []
        peer_section = soup.find("h2", string="Peer comparison")
        if peer_section:
            peer_table = peer_section.find_next("table")
            if peer_table:
                for a in peer_table.find_all("a"):
                    text = a.get_text(strip=True)
                    if text and text not in sector_info:
                        sector_info.append(text)

        return {
            "symbol": symbol,
            "sector_info": ", ".join(sector_info) if sector_info else None,
            "indices": ", ".join(indices) if indices else None
        }

    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return {"symbol": symbol, "sector_info": None, "indices": None}


# --- Read tickers from Excel ---
input_file = "nifty500_valid_tickers.xlsx"
df = pd.read_excel(input_file)

# Assuming the ticker column name is 'Ticker' or similar
ticker_col = [col for col in df.columns if 'ticker' in col.lower()][0]
tickers = df[ticker_col].dropna().tolist()

results = []

for ticker in tickers:
    symbol = ticker.replace(".NS", "").strip().upper()
    print(f"🔍 Fetching {symbol}...")
    data = get_indices_from_screener(symbol)
    results.append(data)
    time.sleep(1.5)  # polite delay to avoid blocking by Screener

# --- Save results ---
output_df = pd.DataFrame(results)
output_df.to_excel("nifty500_screener_indices.xlsx", index=False)
print("\n✅ Done! Saved to nifty500_screener_indices.xlsx")
