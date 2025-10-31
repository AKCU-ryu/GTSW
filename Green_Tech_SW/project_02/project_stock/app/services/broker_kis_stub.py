# app/services/broker_kis_stub.py
# APPKEY(모의투자) 기반 REST 증권사용 스텁; 실제 엔드포인트 연결 전 간단 스켈레톤
from typing import Dict, Any, List
from Green_Tech_SW.project_stock.app.services.broker_base import BrokerBase

class KISBroker(BrokerBase):
    def __init__(self, appkey: str, appsecret: str, vrs_account: str):
        self.appkey = appkey
        self.appsecret = appsecret
        self.account = vrs_account

    def get_price(self, code: str) -> Dict[str, Any]:
        # TODO: /quotations 요청 구현
        return {"code": code, "price": None, "ts": None, "note": "KIS 연결 필요"}

    def order_market(self, code: str, qty: int, side: str) -> Dict[str, Any]:
        # TODO: /orders 요청 구현
        return {"ok": False, "note": "KIS 주문 엔드포인트 구현 필요"}

    def positions(self) -> List[Dict[str, Any]]:
        # TODO: 계좌 평가/잔고 조회
        return []
