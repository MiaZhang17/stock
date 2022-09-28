from excellib import set_excel_color_daily
from stocklib import get_stock_price, get_OTC_price, get_otc, get_investor, get_ratio
from stocklib import cal_bar, cal_KD, check_10days, check_10days_otc, get_trust_today
from stocklib import convert_num

import requests
import shutil
import time
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pandas as pd
import numpy as np
import yfinance as yf
import json
import matplotlib.pyplot as plt
import mplfinance as mpf
import seaborn as sns

ua = UserAgent()
root = '../'
path_trust = root + 'trust/'
path_check = root + 'daily_check/'


# ## 三大法人

file_track = root + 'investors_track_2.xlsx'
shutil.copy2(file_track, file_track.replace('.xlsx', '_backup.xlsx')) # complete target filename given

df_track = pd.read_excel(file_track, index_col=None, engine='openpyxl')
df_track['id'] = df_track['id'].astype(str)

lst_track_tmp = list(set(df_track['id']))
lst_track = lst_track_tmp
print('追蹤股票數：', len(lst_track), lst_track)


d_today = date.today() - timedelta(days=4)

today_tw = d_today - relativedelta(years=1911)
n = 1
if d_today.weekday() == 0:
    n = 3
d_yesterday = d_today - timedelta(days=n)
s_yesterday = (d_today - timedelta(days=n)).strftime("%Y%m%d")
s_today_md = (d_today).strftime("%m/%d")
s_yesterday_md = (d_today - timedelta(days=n)).strftime("%m/%d")
s_today = d_today.strftime("%Y%m%d")

s_today_tw = today_tw.strftime("%Y/%m/%d").lstrip('0')
s_thismonth_tw = today_tw.strftime("%Y/%m").lstrip('0')
print(s_today_tw, s_today, s_yesterday, s_thismonth_tw)
print('今天:', d_today)
# 台灣證券交易所
df_today = get_stock_price(d_today)

df_yesterday = get_stock_price(d_yesterday)

df_investor = get_investor(d_today)

# lst_investor1 = list(df_investor[  (df_investor['trust']>0)].index) # (df_investor['investor']>=0) &
# lst_investor2 = list(df_investor[ (df_investor['investor']>1000) & (df_investor['trust']==0)].index)
# lst_investor = set(lst_investor1 + lst_investor2)
# print(len(lst_investor))
# print(list(lst_investor))


# df_otc_trust = get_otc(d_today)
# df_otc_trust.set_index('代號', inplace=True)
# df_otc_trust['check'] = ''

df_ratio = get_ratio(d_today) # 殖利率、本益比、股價淨值比
# df_ratio_today = df_ratio.copy()
# df_ratio_today = df_ratio_today[df_ratio_today['PER']!='-']
# df_ratio_today['PER'] = df_ratio_today['PER'].astype(float)

# # 殖利率 > 5%、本益比PER<10、股價淨值比 PBR <1
# df_ratio_today = df_ratio_today[(df_ratio_today['dividend%']>5) & (df_ratio_today['PER']<10) & (df_ratio_today['PBR']<1)]

# df_cheap_today = df_today[df_today.index.isin(df_ratio_today.index)]


# df_cheap = pd.concat([df_cheap_today, df_ratio_today], axis=1, join="inner")
# df_cheap = df_cheap[df_cheap['amount']>2000]
# df_cheap.reset_index(inplace=True)
# df_cheap['start'] = s_yesterday_md#today.strftime("%m/%d")

# file_cheap = root + 'cheap.xlsx'
# shutil.copy2(file_cheap, file_cheap.replace('.xlsx', '_backup.xlsx')) # complete target filename given
# df_cheap_old = pd.read_excel(file_cheap, index_col=None, engine='openpyxl')
# df_cheap_old['id'] = df_cheap_old['id'].astype(str)

# df_cheap_new = pd.concat([df_cheap_old, df_cheap])
# df_cheap_new.sort_values('dividend%', ascending=False)

# set_excel_color_daily(df_cheap_new, file_cheap)

def get_stoploss(stock_id):
    series = df_today.loc[stock_id,:]
    # stock_id = series['id']
    if  series['K%'] > 6:
        stop_point = round(series['open'] + (series['close'] - series['open'])/2, 1)
    elif series['K%'] > 2:
        stop_point = series['open']
    elif stock_id in df_track['id'].unique(): # stock_id存在於原本追蹤清單中
        stop_point = df_track[df_track['id']==stock_id]['stoploss'].iloc[0]
    else:
        stop_point = series['open'] # stock_id不存在於原本追蹤清單中
    return stop_point

def set_(df):
    for idx, row in df.iterrows():
        df.at[idx,'stoploss'] = c(row, df_track)

def cal_mean_51018(stock_id):
    time.sleep(0.8)
    data_yf = yf.Ticker(stock_id+'.TW')
    df = data_yf.history(period="1mo")
    df.sort_index(ascending=False, inplace=True)
    
    price_5 = round(np.mean(df['Close'][:5]),2)
    price_10 = round(np.mean(df['Close'][:10]),2)
    price_20 = round(np.mean(df['Close'][:20]),2)
    
    prev_5 = round(np.mean(df['Close'][1:6]),2)
    prev_10 = round(np.mean(df['Close'][1:11]),2)
    prev_20 = round(np.mean(df['Close'][1:21]),2)
    
    slope_5 = round((price_5 - prev_5)*100/price_5, 2)
    slope_10 = round((price_10 - prev_10)*100/price_10, 2)
    slope_20 = round((price_20 - prev_20)*100/price_20, 2) # 除上當日均價 標準化
    
    k, d = cal_KD(stock_id, df, df_track, df_today)
    return pd.Series([price_5, price_10, price_20, slope_5, slope_10, slope_20, k, d])

def get_start_date(stock_id):
    df_ori = df_track[df_track['id']==stock_id]
    if df_ori.empty:  
        return d_today.strftime("%m/%d")
    else:
        return df_ori['start'].iloc[0]


# 今日符合篩選條件，新增至追蹤
# 漲幅 > 1.5%，K棒 > 1%
lst_investor = ['2615']
df_add = df_today.loc[lst_investor,:]
df_add.sort_index(inplace=True)

df_add['rise%'] = round((df_add['close'] - df_yesterday['close'])/df_yesterday['close']*100, 2)  # 漲跌%
df_add['K%'] = round( (df_add['close'] - df_add['open'])/df_add['open']*100, 2 )    # K棒%
df_add = df_add[ (df_add['rise%']>1.5) & (df_add['K%']>1) ]
df_add = check_10days(df_add)
lst_add_ori = list(df_add.index)
print('今日新增:', lst_add_ori)

lst_add = [i for i in df_add.index if i not in list(lst_track)] # 排除掉已經在track裡的股票
df_add = df_add.loc[lst_add,:]



# df_yesterday = df_yesterday[df_yesterday.index.isin(df_add.index)]
# df_yesterday['rise%'] = round((df_yesterday['close'] - df_yesterday['open'])/df_yesterday['close']*100, 2) # 漲跌%
# df_yesterday['K%'] = round( (df_yesterday['close'] - df_yesterday['open'])/df_yesterday['open']*100, 2 )    # K棒%
# df_yesterday['check']=0
# df_yesterday.insert(1, 'date', s_yesterday_md)
# df_yesterday.reset_index(inplace=True)

# 原本追蹤中
df_ori = df_today.loc[lst_track,:]
df_ori['rise%'] = round((df_ori['close'] - df_ori['open'])/df_ori['close']*100, 2) # 漲跌%
df_ori['K%'] = round( (df_ori['close'] - df_ori['open'])/df_ori['open']*100, 2 )    # K棒%

df_today = pd.concat([df_ori, df_add])
print('ori track:',lst_track, ', add：', df_add.index)

# 停損點、上影線、下影線
df_today.insert(1, 'date', d_today.strftime("%m/%d"))
df_today['stoploss'] = df_today.index.to_series().apply(get_stoploss)
df_today[ ['up_bar', 'low_bar'] ] = df_today.apply(lambda x: cal_bar(x.open, x.high, x.low, x.close), axis=1)

# 5, 10 ,20日均線，K,D值
df_today[ ['close5', 'close10', 'close20', 'slope5','slope10', 'slope20', 'Kvalue', 'Dvalue'] ]  = df_today.index.to_series().apply(cal_mean_51018) # 太長了

df = pd.concat([df_today, df_investor, df_ratio], axis=1, join="inner")
df.reset_index(inplace=True)

df_all = pd.concat([df, df_yesterday])
df_all['start'] = df_all['id'].apply(get_start_date)


df_new = pd.concat([df_track, df_all])
df_new.sort_values(['id', 'date'], ascending=[True, False], inplace=True)

# set_excel_color_daily(df_new, file_track)


file_asset = root + 'asset.xlsx'
shutil.copy2(file_asset, file_asset.replace('.xlsx', '_backup.xlsx')) # complete target filename given

txt = root + 'asset.txt'
with open(txt, 'r', encoding='utf8') as f:
    dic = json.loads(f.read())
lst_asset = list(dic.keys())
print(lst_asset)

# 目前持有股票
df_asset = df_new[df_new['id'].isin(lst_asset)]
# set_excel_color_daily(df_asset, file_asset)

# ============================== 先不管上櫃公司 ============================== 
# # 投信買超 上櫃公司
# df_otc_add = df_otc_trust.copy()
# df_otc_add = check_10days_otc(df_otc_add)
# df_otc_add.insert(0, 'date', s_today_md)
# df_otc_add.reset_index(inplace=True)

# path_otc = path_trust + 'otc.xlsx'
# shutil.copy2(path_otc, path_otc.replace('.xlsx', '_backup.xlsx'))
# df_otc_add.to_excel(path_otc, index=False)


# # 投信持股比例
# df_trust_today = get_trust_today()
# lst_trust_today = [str(i) for i in list(df_trust_today['代號'])]
# print(lst_trust_today)

# # 存檔
# path_trust_list = path_trust + 'trust.xlsx'
# shutil.copy2(path_trust_list, path_trust_list.replace('.xlsx', '_backup.xlsx'))

# df_trust_list = pd.read_excel(path_trust_list, engine='openpyxl')
# print('old：', df_trust_list.shape)
# print('new：', df_trust_today.shape)
# df_trust_new = pd.concat([df_trust_list,df_trust_today]).drop_duplicates().reset_index(drop=True)
# print('concat：', df_trust_new.shape)
# df_trust_new.sort_values(['代號', '更新日期'], ascending=[True, False])
# # df_trust_new.to_excel(path_trust_list, index=False)


# lst_trust_add = [i for i in lst_trust_today if i in df_today.index]
# print('投信買超：', len(lst_trust_today), lst_trust_today)
# print('上市公司：', len(lst_trust_add), lst_trust_add)

# df_trusk_add = df_today.loc[lst_trust_add,:]
# df_trusk_add.sort_index(inplace=True)

# # df_trusk_add['rise%'] = round((df_trusk_add['close'] - df_yesterday['close'])/df_yesterday['close']*100, 2)  # 漲跌%
# df_trusk_add['K%'] = round( (df_trusk_add['close'] - df_trusk_add['open'])/df_trusk_add['open']*100, 2 )    # K棒%
# df_trusk_add = df_trusk_add[df_trusk_add['K%']>1] # df_trusk_add['rise%']>1.5) & 
# df_trusk_add = check_10days(df_trusk_add)
# ============================== 先不管上櫃公司 ============================== 

# df_fund = pd.read_excel(root + 'trust/fund_list.xlsx', engine='openpyxl')
# lst_fund = list(df_fund['基金編號'])
# print(lst_fund)

# path_fund_holding = path_trust+'holding.xlsx'
# shutil.copy2(path_fund_holding, path_fund_holding.replace('.xlsx', '_backup.xlsx'))
# df_holding_ori = pd.read_excel(path_trust+'fund_holding.xlsx', engine='openpyxl')
# for fund_id in lst_fund:
# #     fund_id = 'AC0053'
#     url = 'https://finet.landbank.com.tw/w/wr/wr04.djhtm?a={}'.format(fund_id)
#     tables = pd.read_html(url)
#     df_holding = tables[1]

#     col_idx = df_holding[df_holding[0]=='股票名稱'].index[0] # 取得col name index
#     df_holding.columns = df_holding.iloc[col_idx,:]
#     df_holding = df_holding.iloc[col_idx+1:-1,:]

#     df_1 = df_holding.iloc[:,:4]
#     df_2 = df_holding.iloc[:, 4:]
#     df_holding = pd.concat([df_1, df_2], ignore_index=True)
#     df_holding.dropna(inplace=True)
#     df_holding['增減'] = df_holding['增減'].apply(lambda x : x.replace('%', ''))
#     df_holding = df_holding.astype({'比例':float, '增減':float})
#     df_holding = df_holding[df_holding['增減']>0.08]
#     df_holding.insert(0, 'date', s_today_md)
#     df_holding.insert(0, 'stock_id', fund_id)
#     df_holding_ori = df_holding_ori.append(df_holding)
#     time.sleep(0.3)

# # df_holding_new = pd.concat([df_holding_ori,df_holding])
# df_holding_ori.to_excel(path_trust+'fund_holding.xlsx', index=False)


# # for idx, row in df_holding_ori.iterrows():
# #     df_holding_ori.at[idx, 'count'] = df_count.loc[row['股票名稱'], 'count']
# # df_holding_ori.to_excel(path_trust+'fund_holding.xlsx', index=False)
# # df_holding_ori.head(2)


# # df_trust_5days = pd.read_excel(path_trust + 'trust_5days.xlsx', engine='openpyxl')
# # df_trust_5days = df_trust_5days[df_trust_5days['今年買賣超佔發行張數']>2]
# # df_trust_5days = df_trust_5days[df_trust_5days['三個月買賣超佔發行張數']>0]
# # df_trust_5days = df_trust_5days[df_trust_5days['一個月買賣超佔發行張數']>0]

# # df_fund_holding = pd.read_excel(path_trust + 'fund_holding.xlsx', engine='openpyxl')
# # lst_fund_holding = list(df_fund_holding['股票名稱'].unique())
# # print(lst_fund_holding[:5])

# # df_trust_5days = df_trust_5days[df_trust_5days['名稱'].isin(lst_fund_holding)]
# # df_trust_5days = df_trust_5days.iloc[:,1:]
# # df_trust_5days.to_excel(path_trust + 'trust_check.xlsx', index=False)
# # print(list(df_trust_5days['代號']))
# # df_trust_5days


# # # 盤中檢查

# # In[32]:


# # c: 代號
# # o: 開盤價
# # z: 當盤成交價，有時候會沒有
# # v: 成交量
# # y: 昨日收盤
# import requests
# url = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_2330.tw|tse_3008.tw"
# res = requests.get(url)
# res.json()['msgArray']

# df = pd.DataFrame(res.json()['msgArray'])
# df = df[['c','o', 'z', 'v', 'y']]
# df.columns = ['stock_id', 'open', 'price', 'volume', 'yesterday']
# df[df.columns[1:]] = df[df.columns[1:]].astype(float)
# # df = df[df['price']>df['yesterday']] # 今天漲
# df['rise%'] = round((df['price'] - df['yesterday'])/df['yesterday']*100, 2)
# df = df[df['rise%']>2] # 漲幅>2%
# df


# # In[33]:


# # data = yf.Ticker('2603'+'.TW')
# # df_hist = data.history(period="1mo")
# # df_hist.sort_index(ascending=False, inplace=True)
# # df_hist.head(2)


# # # 畫日K線圖、週K線圖

# # In[36]:


# file_name = root + 'stock_20210825_1203.json'
# with open(file_name) as f:
#     dic_stock = json.load(f)

# latest_date_file = datetime.strptime(sorted(dic_stock)[-1], '%Y-%m-%d').date()
# print('目前記錄日期至:',latest_date_file, '新增前:', len(dic_stock), '筆')


# # In[39]:


# import datetime
# import time
# import requests
# from io import StringIO
# import pandas as pd
# import numpy as np

# def crawl_price(date):
#     r = requests.post('http://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + str(date).split(' ')[0].replace('-','') + '&type=ALL')
#     print(str(date).split(' ')[0].replace('-',''))
#     ret = pd.read_csv(StringIO("\n".join([i.translate({ord(c): None for c in ' '}) 
#                                         for i in r.text.split('\n') 
#                                         if len(i.split('",')) == 17 and i[0] != '='])), header=0)
#     ret = ret.set_index('證券代號')
#     ret['成交金額'] = ret['成交金額'].str.replace(',','')
#     ret['成交股數'] = ret['成交股數'].str.replace(',','')
#     return ret


# data_stock = {}
# date_today = d_today # datetime.datetime.now() #- timedelta(days=1)
# n_days = (d_today - latest_date_file).days
# fail_count = 0
# allow_continuous_fail_count = 5
# print('須補天數:', n_days)
# while len(data_stock) < n_days:
#     print('parsing', date_today)
#     # 使用 crawPrice 爬資料
#     try:
#         # 抓資料
#         if date_today.weekday()  in [5,6]:
#             print('Weekend!')
#             date_today -= datetime.timedelta(days=1)
#             continue
#         data_stock[date_today] = crawl_price(date_today)
#         if not str(date_today) in dic_stock.keys():
#             dic_stock[str(date_today)] = data_stock[date_today].to_dict()
#             print("add to dict:", str(date_today))
#         print('success!')
#         fail_count = 0
#     except:
#         # 假日爬不到
#         print('fail! check the date is holiday')
#         fail_count += 1
#         if fail_count == allow_continuous_fail_count:
#             raise
#             break
    
#     # 減一天
#     date_today -= datetime.timedelta(days=1)
#     time.sleep(10)

# print('新增後:', len(dic_stock))
# with open(file_name, 'w') as f:
#     json.dump(dic_stock, f)


# # In[40]:


# def plot_K_chart(df_stock, img_name):
#     import talib
#     img_name = df_stock.iloc[0,0] + img_name
#     # mplfinance內建的漲/跌標記顏色是美國的版本(綠漲紅跌)，先用mplfinance中自訂圖表外觀功能mpf.make_marketcolors()將漲/跌顏色改為台灣版本(紅漲綠跌)，
#     # 接著再將這個設定以mpf.make_mpf_style()功能保存為自訂的外觀。
#     mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
#     s  = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc)

#     sma_10 = talib.SMA(np.array(df_stock['close']), 10)
#     sma_30 = talib.SMA(np.array(df_stock['close']), 30)
    
#     df_stock['k'], df_stock['d'] = talib.STOCH(df_stock['high'], df_stock['low'], df_stock['close'])
#     df_stock['k'].fillna(value=0, inplace=True)
#     df_stock['d'].fillna(value=0, inplace=True)

#     fig = plt.figure(figsize=(20, 8))
#     base_x, base_y, base_w= 0, 0, 1
#     ax3_h = 0.2
#     ax2_h = 0.2
#     ax1_h = 0.5

#     ax1 = fig.add_axes([base_x, ax3_h+ax2_h, base_w, ax1_h])
#     ax2 = fig.add_axes([base_x, ax3_h, base_w, ax2_h])
#     ax3 = fig.add_axes([base_x, base_y, base_w, ax3_h])
#     # ax3 = fig.add_axes([0,0,1,0.2])
    
#     # ax.set_xticks(lst_xticks)
#     # ax.set_xticklabels(df_stock.index[::10])

#     mpf.plot(df_stock, type = 'candle', ax=ax1, style=s, volume=ax3)

#     plt.rcParams['font.sans-serif']=['Microsoft JhengHei'] 
#     ax1.plot(sma_10, label='10日均線')
#     ax1.plot(sma_30, label='30日均線')


#     ax2.plot(df_stock['k'], label='K值')
#     ax2.plot(df_stock['d'], label='D值')

#     lst_xticks = range(0, len(df_stock.index), 5)
#     ax3.set_xticks(lst_xticks)
#     ax3.set_xticklabels(df_stock.index[::5])
#     ax1.legend(loc='upper left', bbox_to_anchor=(0,1));
#     ax2.legend(loc='upper left', bbox_to_anchor=(0,1));
#     ax1.set_title(img_name , fontdict={'fontsize': 32, 'fontweight': 'medium'})
#     plt.savefig(path_check+img_name+'.png',bbox_inches='tight')
#     return fig


# # In[41]:


# df_close = pd.DataFrame({k:d['收盤價'] for k,d in dic_stock.items()}).transpose()
# df_close.index = pd.to_datetime(df_close.index)

# df_open = pd.DataFrame({k:d['開盤價'] for k,d in dic_stock.items()}).transpose()
# df_open.index = pd.to_datetime(df_open.index)

# df_high = pd.DataFrame({k:d['最高價'] for k,d in dic_stock.items()}).transpose()
# df_high.index = pd.to_datetime(df_high.index)

# df_low = pd.DataFrame({k:d['最低價'] for k,d in dic_stock.items()}).transpose()
# df_low.index = pd.to_datetime(df_low.index)

# df_volume = pd.DataFrame({k:d['成交股數'] for k,d in dic_stock.items()}).transpose()
# df_volume.index = pd.to_datetime(df_volume.index)

# lst_stock_id = lst_add_ori
# lst_stock_id


# # In[44]:


# for stock_id in lst_stock_id:
#     thisyear = '2021'
#     print(stock_id)
#     if not stock_id in df_close.keys():
#         print(stock_id, '查無資料')
#         continue
# #     stock_id = '2603'
#     dic_a_stock = {
#         'close':df_close[stock_id][thisyear].dropna().astype(float),
#         'open':df_open[stock_id][thisyear].dropna().astype(float),
#         'high':df_high[stock_id][thisyear].dropna().astype(float),
#         'low':df_low[stock_id][thisyear].dropna().astype(float),
#         'volume': df_volume[stock_id][thisyear].dropna().astype(float),
#     }

#     # Daily DataFrame
#     df_stock = pd.DataFrame(dic_a_stock)
#     df_stock.insert(0,'stock_id', stock_id)
#     df_stock.sort_index(inplace=True)

#     fig_daily = plot_K_chart(df_stock, 'daily')

#     # Weekly DataFrame
#     period_type = '1W'
#     df_week = df_stock.resample(period_type).last()
#     df_week['close'] = df_stock['close'].resample(period_type).last()
#     df_week['open'] = df_stock['open'].resample(period_type).first()
#     df_week['high'] = df_stock['high'].resample(period_type).max()
#     df_week['low'] = df_stock['low'].resample(period_type).min()
#     df_week['volume'] = df_stock['volume'].resample(period_type).sum()

#     fig_weekly = plot_K_chart(df_week, 'weekly')


# # In[ ]:


# # import io
# # io_buf = io.BytesIO()
# # a.savefig(io_buf, format='raw')
# # io_buf.seek(0)
# # img_a = np.reshape(np.frombuffer(io_buf.getvalue(), dtype=np.uint8),
# #                      newshape=(int(a.bbox.bounds[3]), int(a.bbox.bounds[2]), -1))

# # b.savefig(io_buf, format='raw')
# # io_buf.seek(0)
# # img_b = np.reshape(np.frombuffer(io_buf.getvalue(), dtype=np.uint8),
# #                      newshape=(int(b.bbox.bounds[3]), int(b.bbox.bounds[2]), -1))
# # io_buf.close()


# # In[ ]:


# # # img_a = np.fromstring(a.canvas.tostring_rgb(), dtype=np.uint8, sep='')
# # # print(a.canvas.get_width_height()[0] * a.canvas.get_width_height()[-1] * 3)
# # # print(img_a.shape)
# # # img_a = img_a.reshape(a.canvas.get_width_height()[::-1] + (3,))

# # figures = {'a':img_a, 'b':img_b}
# # nrows, ncols = 2, 1
# # fig, axeslist = plt.subplots(ncols=ncols, nrows=nrows)
# # for ind,title in enumerate(figures):
# #     print(ind, title)
# #     axeslist.ravel()[ind].imshow(figures[title])
# # #     axeslist.ravel()[ind].set_title(title)
# # #     axeslist.ravel()[ind].set_axis_off()
# # plt.tight_layout() # optional
# # # ValueError: cannot reshape array of size 3378075 into shape (576,1728,3)


# # In[ ]:


# # df_week = pd.DataFrame(columns=df_stock.columns)
# # df_week


# # In[ ]:


# # from talib import abstract

# # def talib2df(talib_output):
# #     if type(talib_output) == list:
# #         ret = pd.DataFrame(talib_output).transpose()
# #     else:
# #         ret = pd.Series(talib_output)
# #     ret.index = tsmc['close'].index
# #     return ret;

# # talib2df(abstract.STOCH(tsmc)).plot()
# # tsmc['close'].plot(secondary_y=True)


# # In[ ]:





# # In[ ]:


# # import matplotlib.pyplot as plt
# # import mplfinance as mpf
# # %matplotlib inline
# # import seaborn as sns

# # # mplfinance內建的漲/跌標記顏色是美國的版本(綠漲紅跌)，先用mplfinance中自訂圖表外觀功能mpf.make_marketcolors()將漲/跌顏色改為台灣版本(紅漲綠跌)，
# # # 接著再將這個設定以mpf.make_mpf_style()功能保存為自訂的外觀。
# # mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
# # s  = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc)

# # # df_stock.index = df_stock.index.format(formatter=lambda x: x.strftime('%Y-%m-%d')) 
# # df_stock.index.name = 'Date'
# # fig = plt.figure(figsize=(24, 8))

# # # add_axes( x初始座標, y初始座標, 寬, 高 )
# # ax1 = fig.add_axes([0, 0.3, 1, 0.5])
# # ax2 = fig.add_axes([0, 0, 1, 0.3])
# # # ax1 = fig.add_subplot(1, 1, 1)
# # # ax2 = fig.add_subplot(2, 1, 2, sharex=ax1)
# # ax2.set_xticks(range(0, len(df_stock.index), 5))
# # ax2.set_xticklabels(df_stock.index[::5])
# # # mpf.candlestick2_ochl(ax, df_stock['open'], df_stock['close'], df_stock['high'],
# # #                       df_stock['low'], width=0.6, colorup='r', colordown='g', alpha=0.75); 

# # mpf.plot(df_stock, type = 'candle', mav=(10,30), ax=ax1, style=s, volume=ax2) # 必須指定volume一個軸


# # In[ ]:




