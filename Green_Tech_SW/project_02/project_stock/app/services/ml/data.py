# app/services/ml/data.py
import pandas as pd, yfinance as yf

def load_ohlcv(code: str, period="6mo", interval="1d") -> pd.DataFrame:
    df = yf.download(code, period=period, interval=interval, auto_adjust=True, progress=False)
    df = df.rename(columns=str.lower)
    return df.dropna()
