from flask import Flask, request, Response
import requests

app = Flask(__name__)
BASE = "https://bigdata.daejeon.go.kr/openApi/6300000/getOtdjReqstMrhst/getOtdjReqstMrhstlist"
# - const base = 'https://bigdata.daejeon.go.kr/openApi/6300000/getOtdjReqstMrhst/getOtdjReqstMrhstlist';
# + const base = 'http://127.0.0.1:5000/merchants';


@app.get("/merchants")
def merchants():
    # 필요한 쿼리만 전달
    params = {
        "pageNo": request.args.get("pageNo", "1"),
        "numOfRows": request.args.get("numOfRows", "20"),
    }
    if request.args.get("se"): params["se"] = request.args["se"]
    if request.args.get("adstrd_nm"): params["adstrd_nm"] = request.args["adstrd_nm"]

    r = requests.get(BASE, params=params, timeout=10)
    # 응답 그대로 반환 (JSON)
    return Response(r.content, status=r.status_code, content_type=r.headers.get("Content-Type","application/json"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
