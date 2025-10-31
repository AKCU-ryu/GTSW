# GTSW
GreenTech
# 공동 가계부 시스템

이 프로젝트는 총무가 멤버별 지출을 손쉽게 관리할 수 있도록 돕는 웹 기반 공동 가계부입니다. 달력형 메인 화면, 멤버별 전용 페이지, 1/N 분배, 휴일 연동, 머신러닝 기반 영수증 인식 연동 지점을 모두 포함하고 있습니다.

## 주요 기능

- **메인 & 인덱스 구성**: 커버 모션 이후 로그인/회원가입 화면(`메인`), 총무 전용 홈(`base`), 달력과 설정이 결합된 `main_index`, 멤버별 인덱스(`member_index`)를 분리하여 다이어리식 탐색을 제공합니다.
- **달력형 메인 페이지**: 입금/출금 내역을 달력에 표시하고, DB에 저장된 휴일과 기념일 정보를 함께 보여줍니다.
- **멤버 관리**: 이름은 필수, 별명/이메일은 선택으로 멤버를 추가할 수 있습니다. 멤버별 페이지와 잠금(활성/비활성) 토글을 제공합니다.
- **1/N 분배**: 출금 입력 시 선택한 멤버 또는 전체 멤버에게 균등 분배할 수 있습니다.
- **사이드 인덱스**: 멤버별 버튼으로 입금/출금 테이블을 필터링하고, 우측 하단 설정 패널에서 테마/폰트/멤버 추가 등을 설정합니다.
- **영수증 분석 API**: 텍스트 분석과 TensorFlow 기반 이미지 분류를 모두 지원하여, 영수증 촬영본에서도 자동으로 매장 정보를 추출할 수 있습니다.

## 개발 환경 구성

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=manage.py
flask init-data  # 기본 총무 및 휴일 데이터 입력
export SPCDE_SERVICE_KEY=QpWPp9txkmGnVhhlXoHPY8ifB9x/4qxyqYeCH7jFzB82up9cr2dCbJI7veH8NjbhVOzcBFRTKDMgpWQmA/bf2A==
flask sync-spcde --year 2024 --month 02  # 기념일/휴일 동기화 예시
flask run
```

## 공공데이터 포털 휴일/기념일 연동

`flask sync-spcde` 명령은 [SpcdeInfoService](http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService)의 기념일/공휴일 정보를 불러와서 달력에 표시할 수 있도록 DB에 반영합니다. 명령 실행 전 `SPCDE_SERVICE_KEY` 환경 변수에 활용 승인된 서비스 키를 설정해 주세요.

```bash
flask sync-spcde --year 2024 --month 05 --category anniversary --category holiday
```

분류(`--category`)를 지정하지 않으면 기본으로 기념일, 국경일, 공휴일을 모두 가져옵니다.

## 머신러닝 연동 예시

`/api/receipt/analyze` 엔드포인트는 텍스트, JSON, 이미지 업로드를 모두 처리합니다.

- 텍스트/JSON: `app/services/receipt_ai.py`의 정규식 추출기를 사용해 금액·매장명·결제카드를 파싱합니다.
- 이미지(jpg/png 등): `app/services/receipt_ml.py`의 TensorFlow(VGG16 기반) 모델을 불러와 매장 라벨과 신뢰도를 예측합니다.

모델이 준비되어 있지 않다면 아래 명령으로 학습을 수행할 수 있습니다. 학습 데이터는 `data/receipts/train`, `data/receipts/test` 경로에 클래스별 디렉터리 구조로 배치해야 합니다.

```bash
flask train-receipt-model --epochs 10
```

학습이 완료되면 `instance/receipt_classifier.h5`와 레이블 JSON 파일이 생성되며, 이후 이미지 영수증을 업로드하면 예측 결과가 자동으로 응답에 포함됩니다.

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.