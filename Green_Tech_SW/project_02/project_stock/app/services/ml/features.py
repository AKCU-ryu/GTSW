# app/services/ml/features.py
import pandas as pd
import ta

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["sma20"] = out["close"].rolling(20).mean()
    out["sma60"] = out["close"].rolling(60).mean()
    out["rsi14"] = ta.momentum.rsi(out["close"], window=14)
    out["mom20"] = out["close"].pct_change(20)
    return out.dropna()
