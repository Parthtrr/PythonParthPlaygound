import yfinance as yf

stock = yf.Ticker("RELIANCE.NS")

info = stock.info
financials = stock.quarterly_financials
balance = stock.quarterly_balance_sheet
cashflow = stock.quarterly_cash_flow

print(info["trailingPE"], info["returnOnEquity"])
