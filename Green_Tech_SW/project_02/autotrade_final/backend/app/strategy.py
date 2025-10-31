import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from lightgbm import LGBMClassifier

from datafeed.fdr_feed import load_ohlcv_daily
from .features import add_basic_features, label_next_gain

# 간단 IForest(이상치/돌파) + LGBM(상승확률)
def compute_signals_iforest_lightgbm(code: str, start="2019-01-01", end=None):
    df = load_ohlcv_daily(code, start, end)
    df_feat = add_basic_features(df)

    # === Isolation Forest ===
    iforest = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
    score = -iforest.fit_predict(df_feat[["ret1","ret5","vol_chg","hl_spread","ma_ratio"]].values)  # 1=normal, 2=outlier
    sig_if = (score > 1).astype(int)  # outlier=1

    # === LightGBM 분류 ===
    X = df_feat[["ret1","ret5","vol_chg","hl_spread","ma_ratio"]].values
    y = label_next_gain(df_feat, horizon=5).values
    # 학습 가능한 구간만
    valid = ~np.isnan(X).any(axis=1)
    X, y = X[valid], y[valid]
    if len(X) > 100:
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, shuffle=False)
        clf = LGBMClassifier(n_estimators=300, learning_rate=0.05, max_depth=-1, random_state=42)
        clf.fit(Xtr, ytr)
        prob = clf.predict_proba(Xte)[:,1]
        auc = float(roc_auc_score(yte, prob))
        # 마지막 구간 재적용
        prob_full = np.full(valid.shape[0], np.nan)
        prob_full[~np.isnan(prob_full)] = np.nan  # placeholder
        # 간단히 전체에 다시 예측
        prob_all = clf.predict_proba(X)[:,1]
        prob_full = prob_all
    else:
        auc = float("nan")
        prob_full = np.full(X.shape[0], 0.5)

    # 결과 병합
    res = []
    idx = df.index[valid]
    for i, dt in enumerate(idx):
        res.append({
            "ts": dt.strftime("%Y-%m-%d"),
            "iforest_breakout": int(sig_if[valid][i]),
            "rise_prob_lgbm": float(prob_full[i]),
        })
    return df, {"auc": auc, "points": res}
