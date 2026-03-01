import yfinance as yf
import pandas as pd

def tradingview_rsi(symbol, length=14):
    df = yf.download(symbol, interval="1wk", period="5y")

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/length, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]

print(tradingview_rsi("NIFTY_FIN_SERVICE.NS"))