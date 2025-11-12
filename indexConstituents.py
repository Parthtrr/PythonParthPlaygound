import pandas as pd
import requests
import io
import re

# -----------------------------------
# CONFIG
# -----------------------------------
INPUT_FILE = "nifty_indices_yf_tradingview_fixed_final.xlsx"
OUTPUT_FILE = "nifty_indices_with_constituents.xlsx"
BASE_URL = "https://www.niftyindices.com/IndexConstituent/"
# -----------------------------------

# Manual override URLs for indices that don’t follow the standard naming pattern
MANUAL_URLS = {
    "NIFTY FINANCIAL SERVICES": "https://www.niftyindices.com/IndexConstituent/ind_niftyfinancelist.csv",
    "NIFTY FINANCIAL SERVICES 25/50": "https://www.niftyindices.com/IndexConstituent/ind_niftyfinancialservices25-50list.csv",
    "NIFTY PRIVATE BANK": "https://www.niftyindices.com/IndexConstituent/ind_nifty_privatebanklist.csv",
    "NIFTY OIL AND GAS INDEX": "https://www.niftyindices.com/IndexConstituent/ind_niftyoilgaslist.csv",
    "Nifty MidSmall Financial Services": "https://www.niftyindices.com/IndexConstituent/ind_niftymidsmallfinancailservice_list.csv",
    "Nifty MidSmall IT & Telecom": "https://www.niftyindices.com/IndexConstituent/ind_niftymidsmallitAndtelecom_list.csv",
    "Nifty India Corporate Group Index - Aditya Birla Group": "https://www.niftyindices.com/IndexConstituent/ind_nifty_adityabirlalist.csv",
    "Nifty Infrastructure": "https://www.niftyindices.com/IndexConstituent/ind_niftyinfralist.csv",
    "Nifty India Corporate Group Index - Mahindra Group": "https://www.niftyindices.com/IndexConstituent/ind_nifty_mahindralist.csv",
    "Nifty EV & New Age Automotive": "https://www.niftyindices.com/IndexConstituent/ind_niftyEv_NewAgeAutomotive_list.csv",
    "Nifty Housing": "https://www.niftyindices.com/IndexConstituent/ind_niftyhousing_list.csv",
    "Nifty India Consumption": "https://www.niftyindices.com/IndexConstituent/ind_niftyconsumptionlist.csv",
    "Nifty India Infrastructure & Logistics": "https://www.niftyindices.com/IndexConstituent/ind_niftyIndiaInfrastructure_Logistics_list.csv",
    "Nifty Non-Cyclical Consumer": "https://www.niftyindices.com/IndexConstituent/ind_niftynon-cyclicalconsumer_list.csv",
    "Nifty Services Sector": "https://www.niftyindices.com/IndexConstituent/ind_niftyservicelist.csv",
    "Nifty Transportation & Logistics": "https://www.niftyindices.com/IndexConstituent/ind_niftytransportationandlogistics_list.csv",
    "Nifty100 Liquid 15": "https://www.niftyindices.com/IndexConstituent/ind_Nifty100_Liquid15.csv"
}


def normalize_index_name(name: str) -> str:
    """
    Normalize the index name for URL pattern.
    e.g. "Nifty Next 50" -> "niftynext50"
    """
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9]+', '', name)  # remove spaces & special chars
    return name


def try_fetch_csv(index_name: str):
    """
    Try both possible CSV URL formats for the given index name.
    Returns (DataFrame, URL) if successful, else (None, None)
    """

    # 1️⃣ Check if manual URL exists first
    if index_name in MANUAL_URLS:
        urls = [MANUAL_URLS[index_name]]
    else:
        norm = normalize_index_name(index_name)
        urls = [
            f"{BASE_URL}ind_{norm}_list.csv",
            f"{BASE_URL}ind_{norm}list.csv"
        ]

    headers = {"User-Agent": "Mozilla/5.0"}

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200 and "Symbol" in resp.text :
                df = pd.read_csv(io.StringIO(resp.text))
                if not df.empty:
                    return df, url
        except Exception:
            continue
    return None, None


def extract_symbols(df: pd.DataFrame) -> list:
    """
    Extract and format stock symbols from the DataFrame.
    """
    col_candidates = [c for c in df.columns if "symbol" in c.lower()]
    if not col_candidates:
        return []

    symbols = df[col_candidates[0]].dropna().astype(str).tolist()
    # Append .NS for yfinance tickers
    symbols = [s.strip() + ".NS" for s in symbols if s.strip()]
    return symbols


# Step 1: Read the Excel file
index_df = pd.read_excel(INPUT_FILE)

# Step 2: Loop through each index and fetch constituents
constituents_col = []
source_url_col = []

for _, row in index_df.iterrows():
    index_name = str(row["IndexName"]).strip()
    df, url = try_fetch_csv(index_name)

    if df is not None:
        symbols = extract_symbols(df)
        constituents = ", ".join(symbols)
        constituents_col.append(constituents)
        source_url_col.append(url)
        print(f"✅ {index_name}: fetched {len(symbols)} tickers from {url}")
    else:
        constituents_col.append("")
        source_url_col.append("")
        print(f"❌ Could not find index: {index_name}")

# Step 3: Add the results to the DataFrame
index_df["Constituents"] = constituents_col
index_df["SourceURL"] = source_url_col

# Step 4: Save to a new Excel file
index_df.to_excel(OUTPUT_FILE, index=False)

print(f"\n✅ Done! Results written to: {OUTPUT_FILE}")
