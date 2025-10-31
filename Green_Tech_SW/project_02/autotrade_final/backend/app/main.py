import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Literal
from dotenv import load_dotenv
from loguru import logger

from .schemas import OHLCVQuery, OrderRequest
from .storage import Storage
from .strategy import compute_signals_iforest_lightgbm
from datafeed.ohlcv_feed import load_ohlcv_daily
from datafeed.naver_realtime import get_quote_now
from .broker import get_broker

app = FastAPI(title="Autotrade FINAL", version="1.0.0")
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

storage = Storage()
broker = get_broker()

@app.get("/health")
def health():
    return {"ok": True, "broker": broker.name}

@app.post("/ohlcv")
def ohlcv(q: OHLCVQuery):
    try:
        df = load_ohlcv_daily(q.code, q.start, q.end)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(400, f"OHLCV load failed: {e}")
    return {"code": q.code, "rows": len(df), "data": df.reset_index().to_dict(orient="records")}

@app.get("/quote/{code}")
def quote(code: str):
    try:
        q = get_quote_now(code)
        return q
    except Exception as e:
        logger.exception(e)
        raise HTTPException(400, f"Quote failed: {e}")

class SignalQuery(BaseModel):
    code: str
    start: str = "2019-01-01"
    end: Optional[str] = None

@app.post("/signal")
def signal(q: SignalQuery):
    try:
        df, sig = compute_signals_iforest_lightgbm(q.code, q.start, q.end)
        return {"code": q.code, "rows": len(df), "signals": sig}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(400, f"Signal failed: {e}")

@app.post("/orders")
def orders(req: OrderRequest):
    try:
        res = broker.place_order(req, storage)
        return {"ok": True, "broker": broker.name, "result": res}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(400, f"Order failed: {e}")

@app.get("/positions")
def positions():
    return storage.snapshot()

# Static test page
@app.get("/static/index.html")
def static_index():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/static/index.html"))
    return FileResponse(root)
