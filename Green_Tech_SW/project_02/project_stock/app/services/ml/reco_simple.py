# app/services/ml/reco_simple.py
from typing import List, Dict
import pandas as pd
from .data import load_ohlcv
from .features import add_features

def score_row(row) -> float:
    # 간단 점수: 모멘텀 + (sma20>sma60) 보너스 - RSI 과매수 패널티
    score = row["mom20"]
    if row["sma20"] > row["sma60"]:
        score += 0.01
    if row["rsi14"] > 70:
        score -= 0.01
    return float(score)

def score_code(code: str) -> Dict:
    df = load_ohlcv(code)
    f = add_features(df)
    last = f.iloc[-1]
    return {"code": code, "score": score_row(last), "close": float(last["close"])}

def recommend_topn(codes: List[str], n: int = 3):
    rows = [score_code(c) for c in codes]
    out = sorted(rows, key=lambda x: x["score"], reverse=True)[:n]
    return out
