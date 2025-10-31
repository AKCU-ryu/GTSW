import FinanceDataReader as fdr
import pandas as pd

def load_ohlcv_daily(code: str, start="2015-01-01", end=None) -> pd.DataFrame:
    """
    code 예: '000660' (KRX), '005930' 등
    반환 컬럼: ['Open','High','Low','Close','Volume','Change']
    """
    df = fdr.DataReader(code, start, end)
    df.index = pd.to_datetime(df.index)
    return df
