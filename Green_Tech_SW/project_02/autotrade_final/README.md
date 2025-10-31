# Autotrade FINAL (네이버/pykrx/FDR + FastAPI + 간단 ML + 주문(PAPER/KIS 스텁))

파이썬 최신/Anaconda(tf210 등)에서 동작하도록 만든 **최종 스타터**입니다.
- **데이터**: FinanceDataReader(네이버), pykrx(KRX), 네이버 현재가 폴링
- **API**: FastAPI (/ohlcv, /quote, /signal, /orders, /positions)
- **전략(ML)**: IsolationForest 기반 이상치/돌파 감지 + LightGBM 단기상승확률(옵션)
- **주문**: PAPER(메모리 시뮬) 기본 / KIS(REST) 스텁 제공(환경변수 설정 시 활성)
- **프런트(테스트용)**: /static/index.html – 종목코드 입력, 시세/시그널 확인, 페이퍼주문

## 설치
```bash
conda create -n autotrade python=3.10 -y
conda activate autotrade
pip install -r backend/requirements.txt
```
> GPU(TF) 환경(tf210 등)을 쓰는 경우, 해당 환경 활성화 후 `pip install -r backend/requirements.txt`만 추가 설치.

## 환경변수
`backend/.env`를 생성하거나 OS 환경변수를 사용하세요. 예시:
```
BROKER=PAPER          # PAPER | KIS
KIS_APPKEY=YOUR_APPKEY
KIS_APPSECRET=YOUR_APPSECRET
KIS_ACCOUNT=12345678-01
KIS_ISPAPER=true      # 모의투자(true) | 실계좌(false)
KIS_BASEURL=https://openapi.koreainvestment.com:9443   # (KIS 문서 참고)
```

## 실행
```bash
uvicorn backend.app.main:app --reload --port 8000
# 헬스: http://127.0.0.1:8000/health
# 테스트 UI: http://127.0.0.1:8000/static/index.html
```

## 주요 엔드포인트
- `POST /ohlcv` {code, start, end} → FDR 일봉
- `GET /quote/{code}` → 네이버 현재가(비공식)
- `POST /signal` {code, start, end} → 간단 ML 시그널 계산
- `POST /orders` {side, code, qty, priceType, limitPrice?} → PAPER 또는 KIS 스텁
- `GET /positions` → 보유/체결(메모리)

## 주의
- 네이버 엔드포인트는 비공식입니다. 빈도 제한/변경 가능. 예외 처리/백업 소스(FDR/pykrx) 병행 권장.
- KIS 스텁은 **동작 뼈대**만 제공합니다. 실제 주문은 환경변수와 해더/해시키 처리 로직을 완성해야 합니다.
