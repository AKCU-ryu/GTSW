# Autotrade Starter (네이버/pykrx/FDR + FastAPI)

파이썬 최신 버전/아나콘다(tf210 등)에서 동작하도록 구성된 **데이터 피드 + API 스켈레톤**입니다.
- 데이터: FinanceDataReader(네이버), pykrx(KRX), 네이버 현재가 폴링
- API: FastAPI (/ohlcv, /quote)
- (옵션) 키움 워커 샘플 포함 — 필요 없으면 폴더째 삭제하세요.

## 설치
```bash
conda create -n autotrade python=3.10 -y
conda activate autotrade
pip install -r backend/requirements.txt
```
> GPU/TensorFlow 환경(tf210 등)을 사용 중이라면, 해당 환경을 활성화한 뒤 `pip install -r backend/requirements.txt`만 추가로 실행하세요.

## 실행
1) FastAPI 시작
```bash
uvicorn backend.app.main:app --reload --port 8000
# 헬스체크: http://127.0.0.1:8000/health
```

2) OHLCV 조회
```bash
curl -X POST http://127.0.0.1:8000/ohlcv -H "Content-Type: application/json" -d '{"code":"000660","start":"2015-01-01"}'
```

3) 현재가(네이버 폴링)
```bash
curl http://127.0.0.1:8000/quote/000660
```

## 디렉토리
```
autotrade/
├─ backend/
│  ├─ app/
│  │  └─ main.py
│  └─ requirements.txt
├─ datafeed/
│  ├─ fdr_feed.py
│  ├─ pykrx_feed.py
│  └─ naver_realtime.py
└─ scripts/
   └─ test_ws_client.py
```

## 주의
- 네이버 엔드포인트는 비공식이며 빈도 제한/변경 가능성이 있습니다. 예외 처리와 백업 소스를 함께 사용하세요(FDR/pykrx).
- (옵션) 키움 샘플은 PyQt/OCX 제약이 있으니 최신 파이썬 환경만 사용할 경우 삭제하세요.
