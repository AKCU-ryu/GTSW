import FinanceDataReader as fdr
# pip install -U finance-datareader
import matplotlib.pyplot as plt

def get_stock(p_code, p_start, p_end):
    df = fdr.DataReader(p_code, p_start, p_end)
    # df['Close'].plot()
    # plt.show()

    df = df.reset_index()
    seq = df['index'].dt.strftime('%Y-%m-%d')
    x_data = df[['Close']].astype(str)
    x_data['Data'] = seq
    file_nm = f'{p_code}_{p_start.replace("-","")}_{p_end.replace("-","")}.xlsx'
    x_data.to_excel(file_nm)

get_stock('TSLA','2001-01-01','2025-09-30')
# get_stock('TSLA', '2025-08-09', '2025-10-20')

