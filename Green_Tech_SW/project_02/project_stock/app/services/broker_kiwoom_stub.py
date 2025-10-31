# # app/services/broker_kiwoom_stub.py
# # 실제 연결은 PyQt 이벤트루프/ActiveX 제약이 있어 별도 프로세스로 분리 필요
# # 우선 스텁 형태로 인터페이스만 맞춰 둠.
# from typing import Dict, Any, List
# from .broker_base import BrokerBase
#
# class KiwoomBroker(BrokerBase):
#     def __init__(self):
#         # TODO: PyQt5/QAxContainer 기반 별도 런처 구성 후 IPC로 연결
#         raise NotImplementedError("키움 브로커는 별도 런처가 필요합니다.")
#
#     def get_price(self, code: str) -> Dict[str, Any]: ...
#     def order_market(self, code: str, qty: int, side: str) -> Dict[str, Any]: ...
#     def positions(self) -> List[Dict[str, Any]]: ...

# app/services/broker_kiwoom_stub.py  (64bit FastAPI 쪽)
from typing import Dict, Any, List
import requests
from app.services.broker_base import BrokerBase

class KiwoomBroker(BrokerBase):
    def __init__(self, base="http://127.0.0.1:18080"):
        self.base = base

    def get_price(self, code: str) -> Dict[str, Any]:
        code6 = code.split(".")[0]
        r = requests.get(f"{self.base}/price/{code6}", timeout=5)
        r.raise_for_status()
        return r.json()

    def order_market(self, code: str, qty: int, side: str) -> Dict[str, Any]:
        code6 = code.split(".")[0]
        body = {"code": code6, "qty": qty, "side": side}
        r = requests.post(f"{self.base}/order/market", json=body, timeout=5)
        r.raise_for_status()
        return r.json()

    def positions(self) -> List[Dict[str, Any]]:
        # 필요 시 /balance API 추가 구현 (런처에 잔고 조회 TR 붙이면 됨)
        return []
