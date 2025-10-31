from pykrx import stock
import pandas as pd

def load_ohlcv_krx(code: str, start="20150101", end="21000101") -> pd.DataFrame:
    """
    code 예: '000660' (A 접두사 없이)
    반환 컬럼: ['Open','High','Low','Close','Volume']
    """
    df = stock.get_market_ohlcv_by_date(start, end, code)
    df.index = pd.to_datetime(df.index)
    return df.rename(columns={"시가":"Open","고가":"High","저가":"Low","종가":"Close","거래량":"Volume"})
