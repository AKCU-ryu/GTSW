from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

class OHLCVQuery(BaseModel):
    code: str
    start: str = "2015-01-01"
    end: Optional[str] = None

class OrderRequest(BaseModel):
    side: Literal["BUY", "SELL"]
    code: str = Field(..., description="6자리 KRX 코드, ex) 000660")
    qty: int = Field(..., gt=0)
    priceType: Literal["MARKET", "LIMIT"] = "MARKET"
    limitPrice: Optional[float] = None

    @field_validator("limitPrice")
    @classmethod
    def check_limit(cls, v, info):
        priceType = info.data.get("priceType", "MARKET")
        if priceType == "LIMIT" and (v is None or v <= 0):
            raise ValueError("LIMIT 주문은 limitPrice > 0 필요")
        return v
