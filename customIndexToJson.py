import pandas as pd
import yfinance as yf
import json

INPUT_FILE = "customIndex.xlsx"
OUTPUT_FILE = "custom_indices_json.txt"

# Manual ticker corrections
TICKER_CORRECTIONS = {
    "BAJAJ_AUTO.NS": "BAJAJ-AUTO.NS",
    "IIFLSECU.NS": "IIFL.NS"
}

# Read Excel
df = pd.read_excel(INPUT_FILE)

result_dict = {}

for _, row in df.iterrows():
    index_name = str(row['Index']).strip()
    formula = str(row['Formula']).strip()

    # Extract tickers from formula
    raw_tickers = formula.split("+")
    cleaned_tickers = []

    for t in raw_tickers:
        t = t.strip()
        if t.startswith("NSE:"):
            yf_ticker = t.replace("NSE:", "") + ".NS"
        elif t.startswith("BSE_DLY:"):
            yf_ticker = t.replace("BSE_DLY:", "") + ".BO"
        else:
            yf_ticker = t  # fallback if no prefix

        # Apply manual corrections
        yf_ticker = TICKER_CORRECTIONS.get(yf_ticker, yf_ticker)

        # Test ticker with yfinance
        try:
            data = yf.Ticker(yf_ticker).history(period="7d")
            if data.empty:
                print(f"Warning: No data for {yf_ticker}")
                continue
            cleaned_tickers.append(yf_ticker)
        except Exception as e:
            print(f"Error fetching {yf_ticker}: {e}")
            continue

    # Skip index if no valid tickers
    if not cleaned_tickers:
        print(f"Skipping index {index_name}, no valid tickers found.")
        continue

    # Build JSON entry
    key_name = "^" + index_name.upper().replace(" ", "")
    result_dict[key_name] = {
        "Name": index_name,
        "ticker": key_name,
        "constituents": cleaned_tickers,
        "IsCustom": True
    }

# Write JSON to file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(result_dict, f, indent=4)

print(f"Custom indices JSON written to {OUTPUT_FILE}")
