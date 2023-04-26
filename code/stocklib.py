import pandas as pd
import numpy as np

def get_stock_price(d_today):
    s_today = d_today.strftime("%Y%m%d")
    print('取得今日上市股票資訊:', s_today)
    url_today = 'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=html&date={}&type=ALL'.format(s_today)
    
    tables = pd.read_html(url_today)
    df = tables[-1]
    lst_col = [0,1,2,5,6,7,8]
    df = df.iloc[:,lst_col]
    lst_column = ['id', 'name', 'amount', 'open', 'high', 'low', 'close']
    df.columns = lst_column
    df.set_index('id', inplace=True)
    
    df = df[df['open'] !='--']
    # df.iloc[:,1:] = df.iloc[:,1:].astype('float64') #沒用
    df['amount'] = df['amount'].apply(lambda x:x//1000)
    df[df.columns[2:]] = df[df.columns[2:]].astype(float)
    return df

def get_otc(d_today):
    print('取得今日上櫃股票資訊:', d_today)
    from dateutil.relativedelta import relativedelta
    today_tw = d_today - relativedelta(years=1911)
    s_today_tw = today_tw.strftime("%Y/%m/%d").lstrip('0')
    url = r'https://www.tpex.org.tw/web/stock/3insti/sitc_trading/sitctr_result.php?l=zh-tw&t=D&type=buy&d={}&o=htm'.format(s_today_tw)
    tables = pd.read_html(url)
    df_otc_add = tables[0]
    df_otc_add = df_otc_add.iloc[:-1, 1:6]

    lst_col = ['代號','名稱','買進','賣出','買賣超(張)']
    df_otc_add.columns = lst_col
    df_otc_add['買賣超(張)'] = df_otc_add['買賣超(張)'].astype(int)
    df_otc_add = df_otc_add[df_otc_add['買賣超(張)']>200]
    lst_otc = list(df_otc_add['代號'])
    print('投信買超上櫃公司：', len(lst_otc), '\n', lst_otc)
    return df_otc_add

# 取得上櫃公司股價
def get_OTC_price(stock_id):
    import yfinance as yf
    data = yf.Ticker(str(stock_id) + '.TWO')
    df = data.history(period="1d")
    print('上櫃公司股價：', stock_id, len(df))
    return df

def get_investor(d_today):
    s_today = d_today.strftime("%Y%m%d")
    # 換網址了?2023/3/21
    # url = 'https://www.twse.com.tw/fund/T86?response=html&date={}&selectType=ALL'.format()
    url = 'https://www.twse.com.tw/rwd/zh/fund/TWT38U?date={}&response=html'.format(s_today)
    tables = pd.read_html(url)
    df = tables[0]
    # lst_col = [0,4,10,14,17]
    # lst_colname = ['id', 'investor', 'trust', 'dealer_T', 'dealer_F']
    lst_col = [1,5,8]
    lst_colname = ['id', 'investor', 'trust']
    df = df.iloc[:, lst_col]
    df.columns = lst_colname
    df.set_index('id', inplace=True)
    df = df.apply(lambda x:x//1000) # 單位：股，轉換成單位：張
    print('外資, 投信同步買超筆數：',len(df))
    return df

def get_ratio(d_today):
    s_today = d_today.strftime("%Y%m%d")
    url = 'https://www.twse.com.tw/exchangeReport/BWIBBU_d?response=html&date={}&selectType=ALL'.format(s_today)
    tables = pd.read_html(url)
    df = tables[0]
    lst_col = [0,2,4,5]
    lst_colname = ['id', 'dividend%', 'PER', 'PBR'] # 殖利率、本益比、股價淨值比
    df = df.iloc[:, lst_col]
    df.columns = lst_colname
    df = df.copy()
    df['id'] = df['id'].astype(str)
    df.set_index('id', inplace=True)
    return df

def cal_bar(v_open, v_heigh, v_low, v_close):
    bar = abs(v_open-v_close)
    if bar == 0:
        bar = 0.1
    up_leng = v_heigh - max(v_open, v_close)
    low_leng = min(v_open, v_close) - v_low
    up_percent = round(up_leng/bar,2)*100
    low_percent = round(low_leng/bar,2)*100
    return pd.Series([up_percent, low_percent])


def cal_KD(stock_id, df_hist, df_track, df_today):
    df_ori = df_track[df_track['id']==stock_id]
    if df_ori.empty or pd.isnull(df_ori['Kvalue'].iloc[0]):  # 若沒此股票前一天的 K,D值，就不計算 
        return 0,0 
    s = 0
    n = 9
    series = df_today.loc[stock_id,:]
    k_yesterday, d_yesterday = df_ori['Kvalue'].iloc[0], df_ori['Dvalue'].iloc[0] # 27.17, 38.15
    min_9, max_9 = min(df_hist['Low'][s:s+n]), max(df_hist['High'][s:s+n])
    # (今日收盤價 - 最近九天的最低價)/(最近九天的最高價 - 最近九天最低價)
    rsv = (df_hist['Close'].iloc[0] - min_9)/(max_9 - min_9) * 100
    k_today = round((k_yesterday * 2 + rsv) / 3, 2)      # K = 2/3 X (昨日K值) + 1/3 X (今日RSV)
    d_today = round((d_yesterday * 2 + k_today) / 3, 2)  # D = 2/3 X (昨日D值) + 1/3 X (今日K值)
    return k_today, d_today 

def check_10days(df, check='max'): # check今日成交量與過去10日相比是否相對衝高
    import yfinance as yf
    for stock_id, row in df.iterrows():
        data_yf = yf.Ticker(stock_id+'.TW')
        df_hist = data_yf.history(period="1mo")
        if len(df_hist)<10:
            print('查無資料 Hist < 10', len(df_hist))
            df.drop([stock_id], inplace=True)
            continue
        df_hist.sort_index(ascending=False, inplace=True)
        value_yesterday = df_hist['Close'].iloc[1]
        value_today = df_hist['Close'].iloc[0]
        amt_today = df_hist['Volume'].iloc[0]
        flat_percent = 0.06
        flat_low = value_yesterday * (1 - flat_percent)
        flat_high = value_yesterday * (1 + flat_percent)

        flat_10 = np.sum(df_hist['Close'].iloc[1:10].between(flat_low, flat_high))
        # print(stock_id, ',前一天收盤:', round(value_yesterday,2),', Range:', round(flat_low,2), round(flat_high,2), ',盤整天數:', flat_10)
        df.at[stock_id,'check'] = flat_10
        max_value_10 = max(df_hist['High'].iloc[1:10])
        min_value_10 = min(df_hist['Close'].iloc[1:10])
        volume_5avg = np.mean(df_hist.iloc[1:6]['Volume'])

        # 計算布林通道
        n = 20
        his_n = df_hist['Close'].iloc[:n]
        mean_n = np.mean(df_hist['Close'].iloc[:n])
        # std = np.sqrt(np.sum( (his_n - mean_n)**2) / len(his_n))
        std = np.std(his_n)
        boll_up = mean_n + (std * 2)
        boll_down = mean_n - (std * 2)
        boll_diff = boll_up - boll_down
        boll_width = (boll_up - boll_down) / mean_n
        boll_thres = 20
        boll_width_thres = 0.2

        if check == 'max':
            if flat_10 < 7:# 【10天盤整】
                # print(stock_id, ',前7日無盤整, 盤整天數：', flat_10) 
                df.drop([stock_id], inplace=True)
            elif value_today <= max_value_10:  # 【今日收盤 突破 10天盤整】
                # print(stock_id, ',收盤價無突破10天盤整：',round(value_today,1), '小於', round(max_value_10,1))
                df.drop([stock_id], inplace=True)
            elif not ((amt_today > volume_5avg*1.8) and (amt_today < volume_5avg*10)):
                # print(stock_id, f'交易量{round(amt_today/1000000,1)}萬沒突破2倍, 五日平均交易量{round(volume_5avg/1000000,1)}萬')
                df.drop([stock_id], inplace=True)
            elif boll_diff > boll_thres and boll_width > boll_width_thres:
                # print(stock_id, ',布林通道差：', round(boll_diff,2), ',上軌線：', round(boll_up,2), '下軌線：', round(boll_down,2))
                # print(f'{stock_id}, 布林通道差：{round(boll_diff,2)}, 布林帶寬：{round(boll_width,2)}')
                df.drop([stock_id], inplace=True)
            else:
                print(f'{stock_id}, 收盤價：{round(value_today,2)}, 10日內最高價：{round(max_value_10,2)}, 布林通道差：{round(boll_diff,2)}, 布林帶寬：{round(boll_width,2)}')

        elif check == 'min':
            # 檢查今日創新低
            if value_today > min_value_10: 
                # print(stock_id, ',今日收盤價無創新低：',round(value_today,1), '大於', round(min_value_10,1))
                df.drop([stock_id], inplace=True)
            elif boll_diff > boll_thres and boll_width > boll_width_thres:
                # print(stock_id, ',布林通道差：', round(boll_diff,2), ',上軌線：', round(boll_up,2), '下軌線：', round(boll_down,2))
                # print(f'{stock_id}, 布林通道差：{round(boll_diff,2)}, 布林帶寬：{round(boll_width,2)}')
                df.drop([stock_id], inplace=True)
            else:
                print(f'{stock_id}, 收盤價：{round(value_today,2)}, 今日收盤價創新低：{round(value_today,2)}, <= {round(min_value_10,2)}, 布林通道差：{round(boll_diff,1)}')
        else:
            # 檢查昨日是最低點
            if value_yesterday > min_value_10: 
                # print(stock_id, ',昨日收盤價無創新低：',round(value_yesterday,1), '大於', round(min_value_10,1))
                df.drop([stock_id], inplace=True)
            elif boll_diff > boll_thres and boll_width > boll_width_thres:
                # print(stock_id, ',布林通道差：', round(boll_diff,2), ',上軌線：', round(boll_up,2), '下軌線：', round(boll_down,2))
                print(f'{stock_id}, 布林通道差：{round(boll_diff,2)}, 布林帶寬：{round(boll_width,2)}')
                df.drop([stock_id], inplace=True)
            else:
                print(f'{stock_id}, 收盤價：{round(value_today,2)}, 昨日收盤價創新低{round(value_yesterday,2)}, <= {round(min_value_10,2)}, 布林通道差：{round(boll_diff,1)}')

    return df

def check_10days_otc(df): # check今日成交量與過去10日相比是否相對衝高
    for stock_id, row in df.iterrows():
        url_otc_month = 'https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_print.php?l=zh-tw&d={}&stkno={}&s=0,asc,0'.format(s_thismonth_tw, stock_id)
        tables = pd.read_html(url_otc_month)
        df_hist = tables[0]

        df_hist = df_hist.iloc[:-1, :-1]
        lst_col = ['date','Volume','dollar','open','high','low','Close','rise%']
        df_hist.columns = lst_col
        df_hist = df_hist.sort_values('date', ascending=False)
        df_hist[df_hist.columns[1:]] = df_hist[df_hist.columns[1:]].astype(float)

        value_yesterday = df_hist['Close'].iloc[1]
        value_today = df_hist['Close'].iloc[0]
        amt_today = df_hist['Volume'].iloc[0]
        flat_percent = 0.06
        flat_low = value_yesterday * (1 - flat_percent)
        flat_high = value_yesterday * (1 + flat_percent)

        flat_10 = np.sum(df_hist['Close'].iloc[1:10].between(flat_low, flat_high))
        df.at[stock_id,'check'] = flat_10
        max_value_10 = max(df_hist['Close'].iloc[1:10])

        if flat_10 < 8:# 【10天盤整】
            print(stock_id, ',前10日無盤整, 盤整天數：', flat_10) 
            df.drop([stock_id], inplace=True)
        elif value_today <= max_value_10:  # 【今日收盤 突破 10天盤整】
            print(stock_id, ',收盤價無突破10天盤整：',round(value_today,1), '小於', round(max_value_10,1))
            df.drop([stock_id], inplace=True)
        elif sum(amt_today / df_hist.iloc[1:10]['Volume'] <2) > 1:
            print(stock_id, '交易量沒突破2倍, 沒突破次數：', sum(df_hist.iloc[1:10]['Volume']/ amt_today <2))
            df.drop([stock_id], inplace=True)
        else:
            print(stock_id, ',收盤價：', round(value_today,2), '10日內最高收盤價：', round(max_value_10,2))
    return df


def get_trust(d_today):
    # 當日投信買超 上市、上櫃公司
    s_today = d_today.strftime("%Y%m%d")
    url_trust = 'https://www.twse.com.tw/fund/TWT44U?response=html&date={}'.format(s_today)
    tables = pd.read_html(url_trust)
    df_trust = tables[0]
    df_trust = df_trust.iloc[:,[1,5]]
    df_trust.columns = ['stock_id', '買賣超']
    df_trust = df_trust.astype({'stock_id':str, '買賣超':int})
    df_trust.iloc[:,-1] = df_trust.iloc[:,-1].apply(lambda x: round(x/1000,0))
    df_trust = df_trust[df_trust['買賣超']>20]
    df_trust.set_index('stock_id', inplace=True)
    return df_trust

def convert_num(x):
    if '+' in x:
        return  float(x.replace('+',''))
    return float(x)

def get_trust_today():
    path_html = 'D:/Mia/Stock/trust/StockList.html'
    tables = pd.read_html(path_html)
    df_trust_today = tables[0]
    df_trust_today.columns = df_trust_today.iloc[0,:]
    df_trust_today = df_trust_today.iloc[1:,:]
    df_trust_today.dropna(inplace=True)
    df_trust_today['今年買賣超佔發行張數'] = df_trust_today['今年買賣超佔發行張數'].apply(convert_num)
    df_trust_today['一個月買賣超佔發行張數'] = df_trust_today['一個月買賣超佔發行張數'].apply(convert_num)
    df_trust_today['三個月買賣超佔發行張數'] = df_trust_today['三個月買賣超佔發行張數'].apply(convert_num)
    df_trust_today = df_trust_today[(df_trust_today['今年買賣超佔發行張數']>2) & (df_trust_today['三個月買賣超佔發行張數']>0) & (df_trust_today['一個月買賣超佔發行張數']>0)]
    return df_trust_today