# app/services/broker_base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BrokerBase(ABC):
    """브로커 공통 인터페이스(시세/주문)"""

    @abstractmethod
    def get_price(self, code: str) -> Dict[str, Any]:
        """단일 종목 현재가 등 간단 시세"""
        ...

    @abstractmethod
    def order_market(self, code: str, qty: int, side: str) -> Dict[str, Any]:
        """시장가 주문(side: 'buy'|'sell')"""
        ...

    @abstractmethod
    def positions(self) -> List[Dict[str, Any]]:
        """보유 포지션(모의)"""
        ...
