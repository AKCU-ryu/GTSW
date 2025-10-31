import os, time, requests
from loguru import logger
from .schemas import OrderRequest
from .storage import Storage

def _bool_env(v: str) -> bool:
    return str(v).lower() in ["1","true","yes","y","on"]

class KISBroker:
    name = "KIS"

    def __init__(self):
        self.appkey = os.getenv("KIS_APPKEY", "")
        self.appsecret = os.getenv("KIS_APPSECRET", "")
        self.account = os.getenv("KIS_ACCOUNT", "")
        self.paper = _bool_env(os.getenv("KIS_ISPAPER", "true"))
        self.base = os.getenv("KIS_BASEURL", "https://openapi.koreainvestment.com:9443")
        self._access_token = None
        self._token_exp = 0

    def _ensure_token(self):
        if self._access_token and time.time() < self._token_exp - 60:
            return
        # NOTE: 실제 KIS 토큰 발급 엔드포인트/헤더는 문서에 따라 구성해야 합니다.
        url = f"{self.base}/oauth2/tokenP" if self.paper else f"{self.base}/oauth2/token"
        payload = {"grant_type":"client_credentials", "appkey": self.appkey, "appsecret": self.appsecret}
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        self._access_token = data.get("access_token")
        self._token_exp = int(time.time()) + int(data.get("expires_in", 1800))

    def place_order(self, req: OrderRequest, storage: Storage):
        if not (self.appkey and self.appsecret and self.account):
            raise RuntimeError("KIS 환경변수 누락(KIS_APPKEY/SECRET/ACCOUNT). PAPER 모드 또는 환경설정 확인.")
        self._ensure_token()

        # NOTE: 실제 주문: /uapi/domestic-stock/v1/trading/order-cash (KIS 문서 참조)
        # 아래는 스켈레톤. hashkey, tr_id, 헤더 등은 문서대로 구현 필요.
        order_url = f"{self.base}/uapi/domestic-stock/v1/trading/order-cash"
        hdrs = {
            "Content-Type":"application/json",
            "authorization": f"Bearer {self._access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTTC0802U" if self.paper and req.side=="BUY" else "VTTC0801U",  # 예시
        }
        body = {
            "CANO": self.account.split("-")[0],
            "ACNT_PRDT_CD": self.account.split("-")[1],
            "PDNO": req.code,
            "ORD_DVSN": "01" if req.priceType=="LIMIT" else "03",  # 01:지정가, 03:시장가 (예시)
            "ORD_QTY": str(req.qty),
            "ORD_UNPR": "0" if req.priceType=="MARKET" else str(req.limitPrice),
        }
        logger.info(f"[KIS-ORDER] {body}")
        # 실제 전송 주석 처리(스텁)
        # resp = requests.post(order_url, headers=hdrs, json=body, timeout=10)
        # resp.raise_for_status()
        # data = resp.json()

        # 데모: 체결 성공으로 가정 후 로컬에 반영
        fill_price = float(req.limitPrice) if req.priceType=="LIMIT" else 0.0
        storage.record_trade(req.side, req.code, req.qty, fill_price)
        return {"stub": True, "sent": body, "filled": True, "price": fill_price, "qty": req.qty}
