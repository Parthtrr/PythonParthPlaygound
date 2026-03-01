import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import re

# -----------------------------
# Complete list of indices (Broad, Sectoral, Thematic, Strategy)
# -----------------------------
indices = [
    # Broad-Based
    "Nifty 50",
    "Nifty Next 50",
    "Nifty 100",
    "Nifty 200",
    "Nifty Total Market",
    "Nifty 500",
    "Nifty500 Multicap 50:25:25",
    "Nifty500 LargeMidSmall Equal-Cap Weighted",
    "Nifty Midcap150",
    "Nifty Midcap 50",
    "Nifty Midcap Select",
    "Nifty Midcap 100",
    "Nifty Smallcap 250",
    "Nifty Smallcap 50",
    "Nifty Smallcap 100",
    "Nifty Microcap 250",
    "Nifty LargeMidcap 250",
    "Nifty MidSmallcap 400",
    "Nifty India FPI 150",

    # Sectoral
    "NIFTY AUTO",
    "NIFTY BANK",
    "NIFTY CHEMICALS",
    "NIFTY FINANCIAL SERVICES",
    "NIFTY FINANCIAL SERVICES 25/50",
    "Nifty Financial Services Ex Bank",
    "NIFTY FMCG",
    "Nifty HEALTHCARE",
    "NIFTY IT",
    "NIFTY MEDIA",
    "NIFTY METAL",
    "NIFTY PHARMA",
    "NIFTY PRIVATE BANK",
    "NIFTY PSU BANK",
    "NIFTY REALTY",
    "NIFTY CONSUMER DURABLES",
    "NIFTY OIL AND GAS INDEX",
    "Nifty500 Healthcare",
    "Nifty MidSmall Financial Services",
    "Nifty MidSmall Healthcare",
    "Nifty MidSmall IT & Telecom",

    # Thematic / Strategy
    "Nifty India Corporate Group Index - Aditya Birla Group",
    "Nifty Capital Markets",
    "Nifty Commodities",
    "Nifty Conglomerate 50",
    "Nifty Core Housing",
    "Nifty CPSE",
    "Nifty Energy",
    "Nifty EV & New Age Automotive",
    "Nifty Housing",
    "Nifty100 ESG",
    "Nifty100 Enhanced ESG",
    "Nifty100 ESG Sector Leaders",
    "Nifty India Consumption",
    "Nifty India Defence",
    "Nifty India Digital",
    "Nifty India Infrastructure & Logistics",
    "Nifty India Internet",
    "Nifty India Manufacturing",
    "Nifty India New Age Consumption",
    "Nifty India Railways PSU",
    "Nifty India Tourism",
    "Nifty India Select 5 Corporate Groups (MAATR)",
    "Nifty Infrastructure",
    "Nifty India Corporate Group Index - Mahindra Group",
    "Nifty IPO",
    "Nifty Midcap Liquid 15",
    "Nifty MidSmall India Consumption",
    "Nifty MNC",
    "Nifty Mobility",
    "Nifty PSE",
    "Nifty REITs & InvITs",
    "Nifty Rural",
    "Nifty Non-Cyclical Consumer",
    "Nifty Services Sector",
    "Nifty Shariah 25",
    "Nifty India Corporate Group Index - Tata Group",
    "Nifty India Corporate Group Index - Tata Group 25% Cap",
    "Nifty Transportation & Logistics",
    "Nifty100 Liquid 15",
    "Nifty50 Shariah",
    "Nifty500 Shariah",
    "Nifty500 Multicap India Manufacturing 50:30:20",
    "Nifty500 Multicap Infrastructure 50:30:20",
    "Nifty SME Emerge",
    "Nifty Waves",
    "Nifty100 Equal Weight",
    "Nifty100 Low Volatility 30",
    "Nifty 50 Arbitrage",
    "Nifty 50 Futures PR",
    "Nifty 50 Futures TR",
    "Nifty200 Momentum 30",
    "Nifty200 Alpha 30",
    "Nifty100 Alpha 30",
    "Nifty Alpha 50",
    "Nifty Alpha Low Volatility 30",
    "Nifty Alpha Quality Low Volatility 30",
    "Nifty Alpha Quality Value Low Volatility 30",
    "Nifty Dividend Opportunities 50",
    "Nifty Growth Sectors 15",
    "Nifty High Beta 50",
    "Nifty Low Volatility 50",
    "Nifty Top 10 Equal Weight",
    "Nifty Top 15 Equal Weight",
    "Nifty Top 20 Equal Weight",
    "Nifty100 Quality 30",
    "Nifty Midcap150 Momentum 50",
    "Nifty500 Flexicap Quality 30",
    "Nifty500 Low Volatility 50",
    "Nifty500 Momentum 50",
    "Nifty500 Quality 50",
    "Nifty500 Multifactor MQVLv 50",
    "Nifty Midcap150 Quality 50",
    "Nifty Smallcap250 Quality 50",
    "Nifty Total Market Momentum Quality 50",
    "Nifty500 Multicap Momentum Quality 50",
    "Nifty MidSmallcap400 Momentum Quality 100",
    "Nifty Smallcap250 Momentum Quality 100",
    "Nifty Quality Low Volatility 30",
    "Nifty50 Dividend Points",
    "Nifty50 Equal Weight",
    "Nifty50 USD",
    "Nifty50 PR 1x Inverse",
    "Nifty50 PR 2x Leverage",
    "Nifty50 TR 1x Inverse",
    "Nifty50 TR 2x Leverage",
    "Nifty50 Value 20",
    "Nifty200 Value 30",
    "Nifty500 Value 50",
    "Nifty500 Equal Weight",
    "Nifty200 Quality 30",
    "Nifty50 & Short Duration Debt – Dynamic P/B",
    "Nifty50 & Short Duration Debt – Dynamic P/E",
    "Nifty Equity Savings"
]

# -----------------------------
# Helper: convert index name to TradingView style symbol
# -----------------------------
def to_tradingview_symbol(name: str) -> str:
    s = name.upper()
    s = re.sub(r'[^A-Z0-9]+', '_', s)   # Replace spaces and special chars with _
    s = re.sub(r'_+', '_', s)            # Replace multiple _ with single _
    s = s.strip('_')
    return s + ".NS"                      # Append .NS for Yahoo Finance

# -----------------------------
# Test each ticker in yfinance
# -----------------------------
results = []
for name in indices:
    ticker = to_tradingview_symbol(name)
    try:
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end   = datetime.now().strftime("%Y-%m-%d")
        df = yf.download(ticker, start=start, end=end, interval="1d", progress=False)
        status = "SUCCESS" if (df is not None and not df.empty) else "FAIL"
    except Exception as e:
        status = f"FAIL ({e})"
    results.append({
        "IndexName": name,
        "YFTicker": ticker,
        "Status": status
    })
    print(name, "->", ticker, "->", status)

# -----------------------------
# Save results to Excel
# -----------------------------
df_results = pd.DataFrame(results)
df_results.to_excel("nifty_indices_yf_tradingview.xlsx", index=False)
print("✅ Results saved to nifty_indices_yf_tradingview.xlsx")
