# main.py  (단일 파일 스타터)
# 실행:  conda activate kiwoom_web  후  uvicorn main:app --reload --port 8000
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import random, time

# ====== [A] 브로커: Mock (시세/주문) ======
class BrokerBase:
    def get_price(self, code: str) -> Dict[str, Any]: ...
    def order_market(self, code: str, qty: int, side: str) -> Dict[str, Any]: ...
    def positions(self) -> List[Dict[str, Any]]: ...

class MockBroker(BrokerBase):
    def __init__(self):
        self._pos = {}  # 보유 수량 관리

    def get_price(self, code: str) -> Dict[str, Any]:
        px = round(50000 + random.uniform(-1000, 1000), 2)  # 데모용 난수
        return {"code": code, "price": px, "ts": int(time.time())}

    def order_market(self, code: str, qty: int, side: str) -> Dict[str, Any]:
        sign = 1 if side == "buy" else -1
        self._pos[code] = self._pos.get(code, 0) + sign * qty
        return {"ok": True, "code": code, "qty": qty, "side": side, "pos": self._pos[code]}

    def positions(self) -> List[Dict[str, Any]]:
        return [{"code": c, "qty": q} for c, q in self._pos.items()]

broker = MockBroker()  # 지금은 Mock만 사용(키움/REST는 나중에 교체)

# ====== [B] 간단 추천 로직(RSI/모멘텀) ======
# yfinance/ta 설치 시 실제 데이터로 바꿀 수 있음; 일단 의존성 없이 더미 점수 예시
def score_code(code: str) -> Dict[str, Any]:
    # 실제 구현: yfinance로 종가 불러와 features 만들고 점수 산출
    # 여기서는 “모멘텀/RSI 흉내 점수”를 난수로 대체(최소 동작 확인용)
    score = round(random.uniform(-0.05, 0.15), 4)
    close = round(50000 + random.uniform(-1000, 1000), 2)
    return {"code": code, "score": float(score), "close": float(close)}

def recommend_topn(codes: List[str], n: int = 3):
    rows = [score_code(c) for c in codes]
    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows[:n]

# ====== [C] FastAPI 라우팅 ======
app = FastAPI(title="project_stock(minimal)", version="0.0.1")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/api/quotes/{code}")
def price(code: str):
    return broker.get_price(code)

class OrderIn(BaseModel):
    code: str
    qty: int
    side: str  # 'buy' | 'sell'

@app.post("/api/orders/market")
def order_market(req: OrderIn):
    if req.side not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="side는 'buy' 또는 'sell'")
    return broker.order_market(req.code, req.qty, req.side)

@app.get("/api/orders/positions")
def positions():
    return broker.positions()

@app.get("/api/reco/topn")
def reco_topn(codes: List[str] = ["005930.KS","000660.KS","035720.KS"], n: int = 3):
    return {"reco": recommend_topn(codes, n=n)}
