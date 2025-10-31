# pip install requests
import requests


# 응답 상태 코드

response = requests.get("https://www.python.org") # Python 공식 사이트 간단한 GET 요청
print("응답 상태 코드:", response.status_code)