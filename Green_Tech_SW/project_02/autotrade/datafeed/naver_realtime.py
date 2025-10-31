import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_quote_now(code_numeric: str) -> dict:
    """
    code_numeric 예: '000660' (A 없이 6자리)
    주의: 네이버 비공식 엔드포인트이며 변경될 수 있음.
    """
    url = f"https://m.stock.naver.com/api/stock/{code_numeric}/basic"
    r = requests.get(url, headers=HEADERS, timeout=5)
    r.raise_for_status()
    data = r.json()
    return {
        "code": code_numeric,
        "price": float(data.get("closePrice", 0) or 0),
        "change": float(data.get("compareToPreviousClosePrice", 0) or 0),
        "changeRate": float(data.get("fluctuationsRatio", 0) or 0),
        "ts": data.get("localTradedAt"),
        "raw": data,
    }
