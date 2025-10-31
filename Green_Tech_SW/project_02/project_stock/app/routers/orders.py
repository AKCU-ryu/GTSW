# app/routers/orders.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import settings
from app.services.broker_mock import MockBroker
from app.services.broker_kis_stub import KISBroker

router = APIRouter()

class OrderIn(BaseModel):
    code: str
    qty: int
    side: str  # 'buy' | 'sell'

def get_broker():
    if settings.BROKER == "mock":
        return MockBroker()
    elif settings.BROKER == "kis":
        return KISBroker(settings.KIS_APPKEY, settings.KIS_APPSECRET, settings.KIS_VRS_ACCOUNT)
    else:
        raise HTTPException(status_code=501, detail="키움 브로커는 별도 런처 필요")

@router.post("/market")
def order_market(req: OrderIn):
    b = get_broker()
    return b.order_market(req.code, req.qty, req.side)

@router.get("/positions")
def positions():
    b = get_broker()
    return b.positions()
