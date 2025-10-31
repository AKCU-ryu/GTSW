import requests
import json

# 접근토큰 발급
def fn_au10001(data):
	# 1. 요청할 API URL
	host = 'https://mockapi.kiwoom.com' # 모의투자  ← 모의는 이 줄 활성화
	# host = 'https://api.kiwoom.com' # 실전투자      ← 실전은 이 줄 유지
	endpoint = '/oauth2/token'
	url =  host + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8', # 컨텐츠타입
	}

	# 3. http POST 요청
	response = requests.post(url, headers=headers, json=data, timeout=10)  # timeout 권장
	response.raise_for_status()  # HTTP 4xx/5xx 예외 처리

	# 4. 응답 상태 코드와 데이터 출력
	print('Code:', response.status_code)
	print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
	body = response.json()
	print('Body:', json.dumps(body, indent=4, ensure_ascii=False))  # JSON 응답을 파싱하여 출력

	# 5. 후속 호출용 토큰 반환(추가)
	return body.get('token'), body.get('token_type'), body.get('expires_dt')


# 실행 구간
if __name__ == '__main__':
	# 1. 요청 데이터
	params = {
		'grant_type': 'client_credentials',  # grant_type
		'appkey': 'Z7ZqCqvfJzHR4_l9ssyZdVUn73AtngU4ub1r9W3N1r4',     # 앱키
		'secretkey': 'lKTXsF8zC-pEhFK8-il0gtxlu4z1bqeeOOb3p1ukhOU',  # 시크릿키
	}

	# 2. API 실행 (모의=위 주석의 mock host 사용 / 실전=현재 host 유지)
	token, token_type, expires_dt = fn_au10001(data=params)
	print('[RESULT]', token_type, token, expires_dt)
