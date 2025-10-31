# kiwoom_launcher.py  (32bit venv에서 실행)
# 기능: 모의투자 로그인, 현재가 조회, 시장가 주문(매수/매도)
import sys
import time
from flask import Flask, request, jsonify
from pykiwoom.kiwoom import Kiwoom
from PyQt5.QtWidgets import QApplication

app = Flask(__name__)
kiwoom = None  # Kiwoom 인스턴스
account = None

def ensure_login():
    global kiwoom, account
    if kiwoom is None:
        raise RuntimeError("Kiwoom 객체가 초기화되지 않았습니다.")
    # 로그인 상태 확인
    if kiwoom.GetConnectState() == 0:
        raise RuntimeError("키움 OpenAPI 로그인 안됨")
    # 계좌번호
    acc_list = kiwoom.GetLoginInfo("ACCNO")
    if not acc_list:
        raise RuntimeError("계좌번호 조회 실패(모의계좌 권한/로그인 확인)")
    return acc_list[0]

@app.route("/health")
def health():
    try:
        acc = ensure_login()
        return jsonify({"ok": True, "account": acc})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/price/<code>")
def price(code):
    """주식 현재가(코드 6자리, 예: 005930)"""
    ensure_login()
    # TR: opt10001 (주식기본정보요청)
    rqname = "opt10001_req"
    trcode = "opt10001"
    kiwoom.SetInputValue("종목코드", code)
    ret = kiwoom.CommRqData(rqname, trcode, 0, "1001")
    if ret != 0:
        return jsonify({"ok": False, "error": f"CommRqData ret={ret}"}), 500

    # 수신 대기 (간단 폴링)
    time.sleep(0.4)
    price = kiwoom.GetCommData(trcode, rqname, 0, "현재가")  # 문자열, 음수부호 포함
    price = abs(int(price.strip()))
    return jsonify({"ok": True, "code": code, "price": price})

@app.route("/order/market", methods=["POST"])
def order_market():
    """시장가 주문: {code, qty, side} side: buy|sell"""
    ensure_login()
    data = request.get_json(force=True)
    code = data.get("code")
    qty  = int(data.get("qty", 0))
    side = data.get("side")

    if not code or qty <= 0 or side not in ("buy", "sell"):
        return jsonify({"ok": False, "error": "invalid body"}), 400

    acc = ensure_login()
    # SendOrder(품절, 주문유형, 계좌, 주문유형코드, 종목, 수량, 가격, 거래구분, 원주문번호)
    # 주문유형코드: 1=매수, 2=매도 / 시장가 거래구분: "03"
    order_type = 1 if side == "buy" else 2
    ret = kiwoom.SendOrder("market_order", "2001", acc, order_type, code, qty, 0, "03", "")
    if ret != 0:
        return jsonify({"ok": False, "error": f"SendOrder ret={ret}"}), 500
    return jsonify({"ok": True, "code": code, "qty": qty, "side": side})

def main():
    global kiwoom, account
    qt_app = QApplication(sys.argv)          # PyQt 이벤트루프
    kiwoom = Kiwoom()
    # 모의투자 전용 로그인 창 띄움 (수동 로그인 권장)
    kiwoom.CommConnect(block=True)           # 로그인 완료까지 대기
    account = ensure_login()
    print("[KIWOOM] Login OK:", account)
    # Flask는 별 포트에서 서비스 (스레드/리로더 끔)
    app.run(host="127.0.0.1", port=18080, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()
