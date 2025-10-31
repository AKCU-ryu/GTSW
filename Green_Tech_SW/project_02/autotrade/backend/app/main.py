from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datafeed.fdr_feed import load_ohlcv_daily
from datafeed.naver_realtime import get_quote_now

app = FastAPI(title="Autotrade Data Feed", version="0.1.0")

class OHLCVQuery(BaseModel):
    code: str
    start: str = "2015-01-01"
    end: Optional[str] = None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ohlcv")
def ohlcv(q: OHLCVQuery):
    df = load_ohlcv_daily(q.code, q.start, q.end)
    return {"code": q.code, "rows": len(df), "data": df.reset_index().to_dict(orient="records")}

@app.get("/quote/{code}")
def quote(code: str):
    return get_quote_now(code)
