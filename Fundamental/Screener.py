import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO

HEADERS = {"User-Agent": "Mozilla/5.0"}

# =============================
# TICKER LIST (for now only Reliance)
# =============================
TICKERS = ["RELIANCE","ANURAS"]   # later you can add more


def fetch_screener_data(ticker):
    print(f"Fetching {ticker} ...")

    url = f"https://www.screener.in/company/{ticker}/consolidated/"
    html = requests.get(url, headers=HEADERS).text
    soup = BeautifulSoup(html, "html.parser")

    # =============================
    # 1️⃣ Quarterly Results Table
    # =============================
    table = soup.select_one("section#quarters table")
    df_quarterly = pd.read_html(StringIO(str(table)), header=0)[0]

    df_quarterly.rename(columns={df_quarterly.columns[0]: "metric"}, inplace=True)
    df_quarterly["metric"] = (
        df_quarterly["metric"]
        .str.replace("\xa0", " ", regex=False)
        .str.replace("+", "", regex=False)
        .str.strip()
    )

    # =============================
    # 2️⃣ Company Ratios (Market Cap, PE, ROE...)
    # =============================
    ratios = {}
    for li in soup.select("ul#top-ratios li"):
        name = li.select_one("span.name").get_text(strip=True)
        value = li.select_one("span.number")
        if value:
            ratios[name] = value.get_text(strip=True)

    df_ratios = pd.DataFrame(ratios.items(), columns=["Metric", "Value"])

    # =============================
    # 3️⃣ Sector / Industry Hierarchy
    # =============================
    sector_info = {}

    peer_section = soup.select_one("section#peers p.sub")
    if peer_section:
        links = peer_section.find_all("a")
        if len(links) >= 4:
            sector_info = {
                "Broad Sector": links[0].get_text(strip=True),
                "Sector": links[1].get_text(strip=True),
                "Industry Group": links[2].get_text(strip=True),
                "Industry": links[3].get_text(strip=True),
            }

    df_sector = pd.DataFrame(sector_info.items(), columns=["Category", "Value"])

    return df_quarterly, df_ratios, df_sector


# =============================
# MAIN LOOP (for multiple tickers later)
# =============================
for ticker in TICKERS:
    df_quarterly, df_ratios, df_sector = fetch_screener_data(ticker)

    filename = f"{ticker}_fundamentals.xlsx"
    with pd.ExcelWriter(filename) as writer:
        df_quarterly.to_excel(writer, sheet_name="Quarterly Results", index=False)
        df_ratios.to_excel(writer, sheet_name="Key Ratios", index=False)
        df_sector.to_excel(writer, sheet_name="Sector Info", index=False)

    print(f"✅ Saved {filename}")
