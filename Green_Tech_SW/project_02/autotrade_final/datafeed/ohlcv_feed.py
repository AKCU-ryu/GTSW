import pandas as pd
import requests
from pykrx import stock

HEADERS = {"User-Agent":"Mozilla/5.0", "Referer":"https://m.stock.naver.com"}

def _naver_daily(code: str, years: int = 10) -> pd.DataFrame:
    url = f"https://api.stock.naver.com/chart/stock/{code}/daily?period=Y{years}"
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    js = r.json()
    items = js.get("priceInfos") or js.get("data") or []
    rows = []
    for it in items:
        rows.append({
            "Date": it.get("localDate") or it.get("date"),
            "Open": float(it.get("openPrice", 0) or 0),
            "High": float(it.get("highPrice", 0) or 0),
            "Low": float(it.get("lowPrice", 0) or 0),
            "Close": float(it.get("closePrice", 0) or 0),
            "Volume": float(it.get("volume", 0) or 0),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()
    return df

def load_ohlcv_daily(code: str, start: str = "2015-01-01", end: str | None = None) -> pd.DataFrame:
    """
    code: '000660' 등 6자리
    우선 KRX(pykrx), 실패 시 네이버 차트 API fallback
    """
    try:
        df = stock.get_market_ohlcv_by_date(start.replace("-", ""), (end or "21001231").replace("-", ""), code)
        df = df.rename(columns={"시가":"Open","고가":"High","저가":"Low","종가":"Close","거래량":"Volume"})
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        df = _naver_daily(code, years=30)
        if end:
            df = df.loc[(df.index >= pd.to_datetime(start)) & (df.index <= pd.to_datetime(end))]
        else:
            df = df.loc[df.index >= pd.to_datetime(start)]
        return df
