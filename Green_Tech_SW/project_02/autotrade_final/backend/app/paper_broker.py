from .schemas import OrderRequest
from .storage import Storage
from datafeed.naver_realtime import get_quote_now

class PaperBroker:
    name = "PAPER"

    def place_order(self, req: OrderRequest, storage: Storage):
        # 단순 체결: MARKET은 현재가, LIMIT은 지정가 체결로 가정
        price = req.limitPrice if req.priceType == "LIMIT" else float(get_quote_now(req.code)["price"])
        storage.record_trade(req.side, req.code, req.qty, price)
        return {"filled": True, "price": price, "qty": req.qty}
