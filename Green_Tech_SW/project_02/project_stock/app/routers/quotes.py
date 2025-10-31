# app/routers/quotes.py
from fastapi import APIRouter, HTTPException
from app.config import settings
from app.services.broker_mock import MockBroker
from app.services.broker_kis_stub import KISBroker

router = APIRouter()

def get_broker():
    if settings.BROKER == "mock":
        return MockBroker()
    elif settings.BROKER == "kis":
        return KISBroker(settings.KIS_APPKEY, settings.KIS_APPSECRET, settings.KIS_VRS_ACCOUNT)
    else:
        # kiwoom은 별도 런처 필요(스텁)
        raise HTTPException(status_code=501, detail="키움 브로커는 별도 런처 필요")

@router.get("/{code}")
def price(code: str):
    b = get_broker()
    return b.get_price(code)
