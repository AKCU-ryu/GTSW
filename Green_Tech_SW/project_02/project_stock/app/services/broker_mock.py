# app/services/broker_mock.py
from typing import Dict, Any, List
import random, time
from app.services.broker_base import BrokerBase

class MockBroker(BrokerBase):
    def __init__(self):
        self._pos = {}  # code -> qty

    def get_price(self, code: str) -> Dict[str, Any]:
        # 단순 난수 시세(데모)
        px = round(50000 + random.uniform(-1000, 1000), 2)
        return {"code": code, "price": px, "ts": int(time.time())}

    def order_market(self, code: str, qty: int, side: str) -> Dict[str, Any]:
        sign = 1 if side == "buy" else -1
        self._pos[code] = self._pos.get(code, 0) + sign * qty
        return {"ok": True, "code": code, "qty": qty, "side": side, "pos": self._pos[code]}

    def positions(self) -> List[Dict[str, Any]]:
        return [{"code": c, "qty": q} for c, q in self._pos.items()]
