from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Trade:
    side: str
    code: str
    qty: int
    price: float
    ts: str

@dataclass
class Position:
    code: str
    qty: int = 0
    avg_price: float = 0.0

class Storage:
    def __init__(self):
        self.trades: List[Trade] = []
        self.positions: Dict[str, Position] = {}

    def record_trade(self, side: str, code: str, qty: int, price: float):
        ts = datetime.now().isoformat(timespec="seconds")
        self.trades.append(Trade(side, code, qty, price, ts))
        pos = self.positions.get(code, Position(code=code))
        if side == "BUY":
            new_qty = pos.qty + qty
            pos.avg_price = (pos.avg_price * pos.qty + price * qty) / max(new_qty, 1)
            pos.qty = new_qty
        else:
            pos.qty = max(pos.qty - qty, 0)
            if pos.qty == 0:
                pos.avg_price = 0.0
        self.positions[code] = pos

    def snapshot(self) -> dict:
        return {
            "positions": {k: vars(v) for k, v in self.positions.items()},
            "trades": [vars(t) for t in self.trades],
        }
