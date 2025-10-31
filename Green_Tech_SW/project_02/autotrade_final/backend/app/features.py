import pandas as pd
import numpy as np

def add_basic_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ret1"] = df["Close"].pct_change()
    df["ret5"] = df["Close"].pct_change(5)
    df["vol_chg"] = df["Volume"].pct_change().fillna(0)
    df["hl_spread"] = (df["High"] - df["Low"]) / df["Close"].replace(0, np.nan)
    df["ma5"] = df["Close"].rolling(5).mean()
    df["ma20"] = df["Close"].rolling(20).mean()
    df["ma_ratio"] = df["ma5"] / df["ma20"]
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)
    return df

def label_next_gain(df: pd.DataFrame, horizon: int = 5) -> pd.Series:
    fwd = df["Close"].shift(-horizon) / df["Close"] - 1.0
    return (fwd > 0).astype(int)  # 상승=1
