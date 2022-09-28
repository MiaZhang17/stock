import pandas as pd
import numpy as np
from datetime import datetime 
import time
from stocklib import get_OTC_price
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import os
this_year = datetime.now().year
this_month = datetime.now().month
root = 'D:/Mia/Stock/'
dic_quarter = {1:[1, 2, 3], 2:[4, 5, 6], 3:[7, 8, 9], 4:[10, 11, 12]}

df_dividend = pd.read_excel(root + 'company_info.xlsx', engine='openpyxl', dtype={'stock_id':str})
df_dividend.set_index('stock_id', inplace=True)
df_dividend = df_dividend.dropna()

def get_yearly(stock_id, lst_EPS, this_year, stock_name):
    s_this_year = str(this_year)
    t_wait = np.random.randint(5,10)
    print(stock_id, ' wait ', t_wait)
    time.sleep(t_wait)
    import math
    url = 'https://www.twse.com.tw/exchangeReport/FMNPTK?response=html&stockNo={}'.format(stock_id)
    df_yearly = None
    try:
    	df_yearly = pd.read_html(url)[0]
    except Exception as e:
        print(e)
        return
    df_yearly = df_yearly.iloc[:, [0, 4, 6, 8]]
    df_yearly.columns = ['year', 'highest', 'lowest', 'average']
    df_yearly['year'] = df_yearly['year'].apply(lambda x: x+ 1911)
    df_yearly = df_yearly[df_yearly['year']>2014]
    
    df_yearly['year'] = df_yearly['year'].astype(str)
    df_yearly = df_yearly.sort_values('year', ascending=False)
    df_yearly.set_index('year', inplace=True)
    lst_EPS = [item for item in lst_EPS if str(item['year']) in df_yearly.index] # 實際撈到的年份可能比較少
    for item in lst_EPS:
        df_yearly.at[str(item['year']), 'EPS'] = item['eps']
        if item['eps'] == 0:
            print('eps:', item['eps'])
            df_yearly.at[str(item['year']), '本益比_max'] = 0
            df_yearly.at[str(item['year']), '本益比_min'] = 0
        else:
            df_yearly.at[str(item['year']), '本益比_max'] = int(df_yearly.loc[str(item['year']), 'highest'] / item['eps'])
            df_yearly.at[str(item['year']), '本益比_min'] = int(df_yearly.loc[str(item['year']), 'lowest'] / item['eps'])

    pe_max = 0
    pe_min = 0
    eps_y = 0
    if len(lst_EPS) > 0:
        pe_max = math.floor(max(df_yearly['本益比_max'][:4]))
        pe_min = math.ceil(min(df_yearly['本益比_min'][:4]))
        try:
            eps_y = df_yearly.loc[s_this_year, 'EPS']
        except Exception as e:
            print(e)
            s_this_year = str(int(this_year)-1)
            eps_y = df_yearly.loc[s_this_year, 'EPS']
    df_yearly['highest_est'] = eps_y * pe_max
    df_yearly['lowest_est'] = eps_y * pe_min
    df_yearly['本益比_max_avg'] = pe_max
    df_yearly['本益比_min_avg'] = pe_min
    
    df_yearly.reset_index(inplace=True)
    df_yearly.sort_values('year', ascending=False, inplace=True)
    df_yearly.insert(0, 'name', value=stock_name)
    df_yearly.insert(0, 'stock_id', value=stock_id)
    
    # global df_yearly_all
    # df_yearly_all = df_yearly_all.append(df_yearly, ignore_index=True)
    return df_yearly

# # 從月報 篩選出幾家公司
def get_df_monthly(path_month_finance, this_year_TW):
    from glob import glob

    lst_columns = ['出表日期',
    '資料年月',
    '公司代號',
    '公司名稱',
    '產業別',
    '營業收入-當月營收',
    '營業收入-上月營收',
    '營業收入-去年當月營收',
    '營業收入-上月比較增減(%)',
    '營業收入-去年同月增減(%)',
    '累計營業收入-當月累計營收',
    '累計營業收入-去年累計營收',
    '累計營業收入-前期比較增減(%)',
    '備註']
    df_monthly = pd.DataFrame(columns=lst_columns)

    for path in glob(path_month_finance + f'*{this_year_TW}*'):
        df = pd.read_csv(path)
        df_monthly = pd.concat([df_monthly, df])# .append(df, ignore_index=True)
        
    df_monthly.sort_values(['公司代號', '資料年月'], ascending=[True, False], inplace=True)
    print(df_monthly.shape)

    lst_col_million = [5, 6, 7, 10, 11]
    lst_col_round = list(range(5, 13))
    dic_type = { col:float for col in df_monthly.columns[lst_col_round]}

    df_monthly = df_monthly.astype(dic_type)

    # 單位：千>>億
    df_monthly.iloc[:,lst_col_million] = df_monthly.iloc[:,lst_col_million] / 100000
    df_monthly.iloc[:,lst_col_round] = df_monthly.iloc[:,lst_col_round].apply(lambda x: round(x, 2))

    # df_monthly.to_excel(path_monthly + 'monthly_' + s_today + '.xlsx', index=False)
    return df_monthly

def get_df_monthly_check(path_month_finance, income=30, income_growth_MoM=20, income_growth_YoY=20, pre_month=False):
    from datetime import datetime
    global this_month
    global this_year

    this_year = datetime.now().year
    this_month = datetime.now().month
    if pre_month:
    	if this_month == 1:
    		this_year -= 1
    		this_month = 12
    	else:
    		this_month -= 1

    this_month_TW = str(this_year-1911) + '/' + str(this_month-1)
    this_year_TW = str(this_year-1911)
    if this_month == 1:
        this_month_TW = str(this_year-1-1911) + '/12'
    print('目前月報年份：', this_month_TW)


    print('從月報 篩選出幾家公司')
    print('上個月營收 > ' + str(income) + '億', '上個月營收成長 > ' + str(income_growth_MoM)+'%', 'or 去年同季營收成長 > '+str(income_growth_YoY)+'%')
    # # 從月報 篩選出幾家公司
    df_monthly = get_df_monthly(path_month_finance, this_year_TW)

    cols = list(df_monthly.columns)
    print('所有公司筆數：', len(df_monthly['公司代號'].unique()))

    # 上個月營收 > 30億
    # 上個月營收成長 > 20% or 去年同季營收成長 > 20%
    lst_monthly_id = list(df_monthly[(df_monthly['資料年月']==this_month_TW) \
                            & (df_monthly[cols[5]]>income) \
                            & ((df_monthly[cols[8]]>income_growth_MoM) | (df_monthly[cols[9]]>income_growth_YoY))]['公司代號'])
    print('本月觀察公司筆數：', len(lst_monthly_id))

    df_monthly_check = df_monthly[df_monthly['公司代號'].isin(lst_monthly_id)].copy()
    df_monthly_check['公司代號'] = df_monthly_check['公司代號'].astype(str)
    # set_excel_color(df_monthly_check, path_finance + 'monthly_check_' + s_today + '.xlsx')

    return df_monthly_check

def get_df_quarterly_ori(stock_id):
    import ssl
    url = 'https://www.above.tw/excel/TProStkFinReport/Income?sym={}'.format(stock_id) # 單位(億)
    ssl._create_default_https_context = ssl._create_unverified_context  # 因出現 CERTIFICATE_VERIFY_FAILED] 

    df = pd.read_excel(url, engine='openpyxl', skiprows=1)
    df = df.set_index(df.columns[0])

    df = df.transpose()

    # 移除千位數符號，轉換成float (原本就是float的Series, 要先轉成astype(str))
    df = df.apply(lambda x: x.astype(str).str.replace(',', ''))
    dic_col = {col:float for col in df.columns}
    if len(df) ==1 :
        print('No data')
        return
    df = df.astype(dic_col)
    df.insert(0, 'year', value=df.index.to_series().apply(lambda x: int(x[:4])))
    return df

def get_equity(stock_id, year, season):
    print('get_equity：', stock_id, year, season)
    ua = UserAgent()
    agent = ua.random
    url = 'https://mops.twse.com.tw/server-java/t164sb01?step=1&CO_ID={}&SYEAR={}&SSEASON={}&REPORT_ID=C'.format(stock_id, year, season)

    headers = {'user-agent':agent}
    res = requests.get(url, headers=headers)
    res.encoding = 'big5'
    soup = BeautifulSoup(res.text, 'lxml')
    tables = soup.find_all('table')
    if len(tables)==0:
        print(stock_id, '查無資料')
        return 0
    df = pd.read_html(str(tables[0]))[0]
    if len(df) < 10:
        if len(tables) > 1:
            df = pd.read_html(str(tables[1]))[0]
        else:
            return 0

    col_index = 0 # 設為index的column
    for i in range(len(df.columns)):
        if type(df.iloc[0,i]) == str:
            if '資產' in df.iloc[0,i]:
                col_index = i
    df = df.set_index(df.columns[col_index])
    # 權益總計 Total equity、權益總額 Total equity、權益總計
    df_equity = df[(df.index.str.contains("權益總") | df.index.str.contains("權益 Equity")) \
               & ~df.index.str.contains("負債") & ~df.index.str.contains("權益 Equity ")]
    if len(df_equity) == 0:
        df_equity = df.loc['權益',:].iloc[[-1],:]
    equity = float(df_equity.iloc[0,col_index]) / 100000 # 千元>億
    return equity

# def get_df_quarterly_equity(stock_id):
#     path_equity = root + 'equity/quarterly_equity_{}.xlsx'.format(stock_id)
#     df = get_df_quarterly_ori(stock_id)
#     df['股東權益'] = 0
#     for idx, row in df.iloc[:16, :].iterrows():
#         df.at[idx, '股東權益'] = get_equity(stock_id, idx[:4], idx[-1])
#         # t_wait = np.random.randint(2, 5)
#         # time.sleep(t_wait)
#     df.to_excel(path_equity)
#     return df

def get_df_quarterly_equity(stock_id):
    path_equity = root + 'equity/quarterly_equity_{}.xlsx'.format(stock_id)
    if os.path.exists(path_equity):
        print(stock_id, '已存在')
        df_equity_ori = pd.read_excel(path_equity, engine='openpyxl', dtype={'stock_id':str})
        df_equity_ori = df_equity_ori.set_index(df_equity_ori.columns[0])
    df = get_df_quarterly_ori(stock_id)
    df['股東權益'] = 0
    for idx, row in df.iloc[:16, :].iterrows():
        equity_cal = 0
        if os.path.exists(path_equity) and idx in df_equity_ori.index:
            equity_cal = df_equity_ori.loc[idx, '股東權益']
        else:
            print(stock_id, 'add new equity', idx)
            equity_cal = get_equity(stock_id, idx[:4], idx[-1])
        df.at[idx, '股東權益'] = equity_cal
    df.to_excel(path_equity)
    return df

def get_finance_col(df):
    df['業外收入'] = df['稅前淨利'] - df['營業利益']
    df['母公司(%)'] = round(df['歸屬母公司淨利(損)'] / df['稅前淨利']*100, 1)
    df['稅率'] = round(df['所得稅費用'] / df['稅前淨利'], 2)
    df['稅後淨利'] = df['稅前淨利'] * (1 - df['稅率'])
    df['毛利率(%)'] = round(df['營業毛利'] / df['營業收入']*100, 1)
    df['營益率(%)'] = round(df['營業利益'] / df['營業收入']*100, 1)
    df['淨利率(%)'] = round(df['稅前淨利'] / df['營業收入']*100, 1)
    return df

def get_df_quarterly(stock_id):
    df = get_df_quarterly_ori(stock_id)
    if not df is None:
        df = get_finance_col(df)
    return df

def get_df_quarterly_all():
    lst_columns = ['stock_id','name', 'quarter', '營業收入', '營業成本', '營業毛利', '營業毛利(毛損)淨額', '營業費用', '營業利益', '稅前淨利', '所得稅費用',
        '歸屬母公司淨利(損)', '每股盈餘(元)', '業外收入', '母公司(%)', '稅率', '稅後淨利', '毛利率(%)',
        '營益率(%)', '淨利率(%)', '股價', 'EPS(Y)', '本益比(Y)', '股利_avg', '股利(%)',
        '殖利率(%)', '2020', '2019', '2018', '2017', '2016', '2015']
    df_quarterly_all = pd.DataFrame(columns=lst_columns)
    return df_quarterly_all

def get_df_yearly(stock_id, df_quarterly):
    # df = get_df_quarterly_equity(stock_id)
    df_y = df_quarterly.groupby('year').sum()
    df_y = get_finance_col(df_y)
    
    df_dividend['year'] = df_dividend['year'].astype(int)
    if stock_id in  df_dividend.index:      
        df_dividend_y = df_dividend.loc[stock_id,:].set_index('year')
        df_dividend_y = df_dividend_y[['發行股數(千股)', 'cash']]
        df_all = pd.concat([df_y, df_dividend_y], axis=1, join="inner")
        df_all = df_all.sort_index(ascending=False)
        df_all['現金股利_成長(%)'] = round((df_all['cash']-df_all['cash'].shift(periods=-1))/df_all['cash'].shift(periods=-1)*100,1)
    else:
        print('上櫃公司')
        df_all = df_y.copy()
        df_all = df_all.sort_index(ascending=False)
        df_all['現金股利_成長(%)'] = 0
    if 'cash' in df_all.columns:
        df_all['現金股利(%)'] = round((df_all['cash'])/df_all['每股盈餘(元)'].shift(periods=-1) * 100,1)
    else:
        df_all['現金股利(%)'] = 0

    this_year = max(df_y.index)
    lst_quarter = [str(this_year) + 'Q' + str(i) for i in range(1,5)]
    num_quarter = len(df_quarterly[df_quarterly.index.isin(lst_quarter)]) # 已公布的季報數量
    EPS_year = round(sum(df_quarterly[df_quarterly.index.isin(lst_quarter)]['每股盈餘(元)']) / num_quarter * 4, 2)
    df_all['EPS(Y)'] = df_all['每股盈餘(元)']
    df_all.at[this_year, 'EPS(Y)'] = EPS_year

    df_all['營業收入_成長(%)'] = round((df_all['營業收入']-df_all['營業收入'].shift(periods=-1))/df_all['營業收入'].shift(periods=-1) * 100,1)

    df_all['稅後淨利_成長(%)'] = round((df_all['稅後淨利']-df_all['稅後淨利'].shift(periods=-1))/df_all['稅後淨利'].shift(periods=-1) * 100,1)

    df_all['EPS(Y)_成長(%)'] = round((df_all['EPS(Y)']-df_all['EPS(Y)'].shift(periods=-1))/df_all['EPS(Y)'].shift(periods=-1) * 100,1)

    df_all['毛利率_成長(%)'] = round((df_all['毛利率(%)']-df_all['毛利率(%)'].shift(periods=-1))/df_all['毛利率(%)'].shift(periods=-1) * 100,1)

    df_all['股東權益'] = round(df_all['股東權益']/4, 1)

    df_all['ROE(%)'] = round(df_all['稅後淨利']/df_all['股東權益'] * 100, 1)

    path_equity = root + 'equity/yearly/yearly_equity_ori_{}.xlsx'.format(stock_id)
    df_all.to_excel(path_equity)
    return df_all

# 寫入歷年EPS、本益比，估算今年股價min, max範圍
def get_df_yearly_all():
    lst_columns = ['stock_id', 'name', 'year', 'highest', 'lowest', 'average', 'EPS', '本益比_max', '本益比_min']
    df_yearly_all = pd.DataFrame(columns=lst_columns)
    return df_yearly_all


def get_company_dividen(lst_stock_id):
    import requests
    from bs4 import BeautifulSoup
    from fake_useragent import UserAgent
    from datetime import date 
    from tqdm import tqdm

    root = 'D:/Mia/Stock/'
    path_dividen = root + 'company_dividen.xlsx'
    df_dividen_all = pd.read_excel(path_dividen, engine='openpyxl', dtype={'stock_id':str})

    ua = UserAgent()
    agent = ua.random
    for stock_id in tqdm(lst_stock_id):
        df_exist = df_dividen_all[df_dividen_all['stock_id']==stock_id]
        if len(df_exist) > 0:
            if len(df_exist[df_exist['year']==this_year]) > 0:
                continue
                
        t_wait = np.random.randint(15, 25)
        print(stock_id, 'wait:', t_wait)
        url = 'https://goodinfo.tw/StockInfo/StockDetail.asp?STOCK_ID={}'.format(stock_id)

        headers = {'user-agent':agent}
        res = requests.get(url, headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'lxml')

        tb = soup.find(id='FINANCE_DIVIDEND')
        
        try:
            df_dividen = pd.read_html(str(tb))[0]
        except:
            print(stock_id, 'Error No tables found')
            continue
        df_dividen = df_dividen.iloc[:,:-1]
        df_dividen.columns = ['year', 'cash', 'stock']
        df_dividen.drop(df_dividen.index[:3], inplace=True)
        df_dividen.drop(df_dividen.index[-1], inplace=True)
        df_dividen['year'] = df_dividen['year'].astype(int)
        df_dividen = df_dividen[df_dividen['year']>2014]

        if len(df_exist) > 0:
            df_dividen = df_dividen[~df_dividen['year'].isin(df_exist['year'])]
            print('Add this year', this_year)
            print(df_dividen)

        df_dividen.insert(0, 'stock_id', value=stock_id)
        df_dividen_all = df_dividen_all.append(df_dividen)
        time.sleep(t_wait)
        
    df_dividen_all.to_excel(path_dividen, index=False)

    # 合併發行股數 與 歷年股利Excel
    path_company = root + 'company_list.xlsx'
    path_dividen = root + 'company_dividen.xlsx'
    path_company_info = root + 'company_info.xlsx'
    import shutil
    shutil.copy2(path_company_info, path_company_info.replace('.xlsx', '_backup.xlsx'))

    df_1 = pd.read_excel(path_company, engine='openpyxl')
    df_2 = pd.read_excel(path_dividen, engine='openpyxl')
    print(df_1.shape)
    print(df_2.shape)
    df_all = df_1.set_index('stock_id').join(df_2.set_index('stock_id'))
    print(df_all.shape)
    df_all.reset_index(inplace=True)
    df_all.to_excel(path_company_info, index=False)



def get_this_quarter():
    for k, v in dic_quarter.items():
        if this_month-1 in v:
            return k

def get_quarter_income(stock_id, num_year, quarter): # 單位：億
    import os
    path_month_finance = root + 'monthly_finance/'
    lst_income = []
    income_sum = 0
    for mon in dic_quarter[quarter]:
        file_monthly = path_month_finance + 't21sc03_{year}_{month}.csv'.format(year=num_year-1911, month=mon)
        if os.path.exists(file_monthly):
            df_month = pd.read_csv(file_monthly, dtype={'公司代號':str})
            df_month = df_month[df_month['公司代號']==stock_id]
            # 單位：千>>億
            if len(df_month) > 0:
                lst_income.append(round(df_month.iloc[0,5] / 100000, 2))
    if len(lst_income)>0:
        income_sum = sum(lst_income) / len(lst_income) * 3
    return income_sum

def get_estimate_income(df, stock_id, num_year, quarter):
    import os
    path_month_finance = root + 'monthly_finance/'
    stock_name = df.iloc[0,1]
    real_income = 0
    expect_income = df.iloc[0,3] # 預估季營收
    for mon in dic_quarter[quarter]:
        file_monthly = path_month_finance + 't21sc03_{year}_{month}.csv'.format(year=num_year-1911, month=mon)
        if os.path.exists(file_monthly):
            df_month = pd.read_csv(file_monthly, dtype={'公司代號':str})
            df_month = df_month[df_month['公司代號']==stock_id]
            # 單位：千>>億
            if len(df_month) > 0:
                df_new = pd.DataFrame([{'stock_id':stock_id, 'name':stock_name, 'quarter':str(num_year)+'Q'+str(quarter)+str(mon)}])
                df_new['營業收入'] = round(df_month.iloc[0,5] / 100000, 2)
                real_income += round(df_month.iloc[0,5] / 100000, 2)
                df = df.append(df_new)
    df_new = pd.DataFrame([{'stock_id':stock_id, 'name':stock_name, 'quarter':str(num_year)+'Q'+str(quarter)+str(mon)}])
    df_new['營業收入'] = round(expect_income - real_income, 2)
    df = df.append(df_new)
    return df.sort_values('quarter', ascending=False)

def get_quarter_finance(stock_id, df, year, quarter, df_company_stock_num, df_today):
    # 估算新一季的EPS
    df_new = pd.DataFrame([{'stock_id':stock_id, 'name':df.iloc[0,1], 'quarter':str(year)+'Q'+str(quarter)}])

    num_100million = 100000000 # 億
    if not stock_id in df_today.index: # 上櫃公司
        return df_new
    
    stock_num = 0 
    if stock_id in df_company_stock_num.index:
        stock_num = df_company_stock_num.loc[stock_id, '發行股數(千股)']
    df_new['普通股數'] = stock_num

    # 手動填寫
    # 用月報的營收 估算季報的營收
    df_new['營業收入'] = get_quarter_income(stock_id, year, quarter)

    df_new['營業費用'] = round(np.mean(df.loc[df.index[:3],'營業費用']),2) # 近三季的平均 營業費用
    df_new['業外收入'] = round(np.mean(df.loc[df.index[:3],'業外收入']),2) # 近三季的平均 業外收入
    df_new['稅率'] = round(np.mean(df.loc[df.index[:3],'稅率']),2) # 近三季的平均 稅率
    df_new['毛利率(%)'] = round(np.mean(df.loc[df.index[:3],'毛利率(%)']),2) # 近三季的平均 毛利率
    df_new['所得稅費用'] = round(np.mean(df.loc[df.index[:3],'所得稅費用']),2) # 近三季的平均 所得稅費用
    df_new['歸屬母公司淨利(損)'] = round(np.mean(df.loc[df.index[:3],'歸屬母公司淨利(損)']),2) # 近三季的平均 歸屬母公司淨利(損)
    df_new['母公司(%)'] = round(np.mean(df.loc[df.index[:3],'母公司(%)']),2) # 近三季的平均 母公司(%)
    cash_pct = 0
    if len(df) > 4:
        cash_pct = round(np.mean(df.loc[df.index[4],'股利(%)']),2) 
    df_new['股利(%)'] = cash_pct
    
    # 計算
    df_new['營業毛利'] = round(df_new.loc[0, '營業收入'] * df_new.loc[0, '毛利率(%)']/100,2) 
    df_new['營業利益'] = round(df_new.loc[0, '營業毛利'] - df_new.loc[0, '營業費用'],2) 
    df_new['稅前淨利'] = round(df_new.loc[0, '營業利益'] + df_new.loc[0, '業外收入'],2) 
    df_new['稅後淨利'] = round(df_new.loc[0, '稅前淨利'] * (1 - df_new.loc[0, '稅率']),2) 
    stock_eps = 0 
    if stock_id in df_company_stock_num.index:
        stock_eps = round(df_new.loc[0, '稅後淨利'] * num_100million / df_new.loc[0, '普通股數'],2)
    df_new['每股盈餘(元)'] = stock_eps
    eps_prep = 0
    if quarter > 1:
        eps_prep = sum(df.loc[df.index[:quarter-1],'每股盈餘(元)'])
    df_new['EPS(Y)'] = round((df_new.loc[0, '每股盈餘(元)']+eps_prep)/quarter*4 ,2) # 估算整年EPS
    df_new['股利_avg'] = round(round(df_new.loc[0, 'EPS(Y)'],3) * round(df_new.loc[0, '股利(%)'],3)/100, 2) 
    df_new['股價'] = df_today.loc[stock_id, 'close']
    if df_new.loc[0, 'EPS(Y)'] > 0:
        df_new['本益比(Y)'] = round(df_new.loc[0, '股價'] / df_new.loc[0, 'EPS(Y)'], 0) 
    else:
        df_new['本益比(Y)'] = 0
    rate = 0
    if df_new.loc[0, '股價'] > 0:
        rate = round(df_new.loc[0, '股利_avg'] / df_new.loc[0, '股價']*100, 2) 
    df_new['殖利率(%)'] = rate
    return df_new


# # 計算歷年同季的營收成長率
def set_growth_eps(df, df_today, stock_id):
    # # 取得過去3年平均現金股利
    df_dividend = pd.read_excel(root + 'company_info.xlsx', engine='openpyxl', dtype={'stock_id':str})
    df_dividend.set_index('stock_id', inplace=True)
    for idx, row in df.iterrows():
        this_year = int(idx[:4])
        
        # 估算年度EPS
        lst_quarter = [str(this_year) + 'Q' + str(i) for i in range(1,5)]
        num_quarter = len(df[df.index.isin(lst_quarter)]) # 已公布的季報數量
        EPS_year = round(sum(df[df.index.isin(lst_quarter)]['每股盈餘(元)']) / num_quarter * 4, 2)
        
        if not stock_id in df_today.index:
            print(stock_id, '不在今日股價清單上')
            df_OTC = get_OTC_price(stock_id)
            stock_price = 0
            if len(df_OTC) > 0:
                stock_price = df_OTC.iloc[0]['Close']
            df.loc[idx, '股價'] = stock_price
        else:
            df.loc[idx, '股價'] = df_today.loc[stock_id, 'close']
        df.loc[idx, 'EPS(Y)'] = EPS_year
        df.loc[idx, '本益比(Y)'] = round(df.loc[idx, '股價'] / EPS_year,2) # 本益比 = 股價 / 年度EPS
        if (this_year > 2014) & (list(df_dividend.index).count(stock_id)>1) :
            y = this_year 
            if not  stock_id in df_dividend[df_dividend['year']==this_year].index:
                y = this_year - 1
            df.loc[idx, '股利_avg'] = df_dividend[df_dividend['year']==y].loc[stock_id, 'cash']
        else:
            df.loc[idx, '股利_avg'] = 0

        lst_year = set(df.index.to_series().apply(lambda x: int(x[:4])))
        min_year = min(lst_year)   
        # 算過去5年同季的成長率
        for i in range(1,6):
            old_year = this_year - i
            if old_year < min_year+1:
                break
            old_quarter = idx.replace(str(this_year),str(old_year))

            new_income = df.loc[idx, '營業收入']
            old_income = df.loc[old_quarter, '營業收入']
            if old_income == 0:
                growth = 0
            else:
                growth = round((new_income / old_income - 1) * 100,1)
            
            df.loc[idx, str(old_year)] = growth

    for idx, row in df.iterrows():
        this_year = int(idx[:4])
        # 今年股利 是根據去年EPS發的
        eps_lastyear = 0
        if (str(this_year-1)+'Q4') in df.index:
            eps_lastyear = df.loc[str(this_year-1)+'Q4', 'EPS(Y)']
            df.loc[idx, '股利(%)'] = round(df.loc[idx, '股利_avg'] / eps_lastyear*100, 1)
        
        rate = 0
        if df.loc[idx, '股價'] > 0:
            rate = round(df.loc[idx, '股利_avg'] / df.loc[idx, '股價']*100, 1)
        df.loc[idx, '殖利率(%)'] = rate
    return df

def check_5_years(stock_id, df_quarterly, df_today, check=False, threshold=-20):
    df_y = get_df_yearly(stock_id, df_quarterly)
    df_y = df_y.apply(lambda x : round(x,1))
    this_year = df_y.index[0]
    lst_quarter = [str(this_year) + 'Q' + str(i) for i in range(1,5)]
    num_quarter = len(df_quarterly[df_quarterly.index.isin(lst_quarter)]) # 已公布的季報數量
    EPS_year = round(sum(df_quarterly[df_quarterly.index.isin(lst_quarter)]['每股盈餘(元)']) / num_quarter * 4, 2)
    df_y['EPS(Y)'] = df_y['每股盈餘(元)']
    df_y.at[this_year, 'EPS(Y)'] = EPS_year
    lst_EPS = [{'year':y, 'eps': df_y.loc[y, 'EPS(Y)']} for y in df_y.index]
    df_yearly = get_yearly(stock_id, lst_EPS, this_year, "") 

    if not 'cash' in df_y.columns:
        df_y['cash'] = 0
    if not '現金股利_成長(%)' in df_y.columns:
        df_y['現金股利_成長(%)'] = 0

    if check:
        df_y = df_y.fillna(0)
        df_5 = df_y[1:5]
        if len(df_5[(df_5['營業收入_成長(%)']<threshold)])>0:
            print('營業收入_成長(%)<', threshold)
            return
        elif len(df_5[(df_5['稅後淨利_成長(%)']<threshold)])>0:
            print('稅後淨利_成長(%)<', threshold)
            return 
        elif len(df_5[(df_5['EPS(Y)_成長(%)']<threshold)])>0:
            print('EPS(Y)_成長(%) <', threshold)
            return
        elif len(df_5[(df_5['毛利率_成長(%)']<threshold)])>0:
            print('毛利率_成長(%)<', threshold)
            return
        elif len(df_5[(df_5['現金股利_成長(%)']<threshold)])>0:
            print('現金股利_成長(%)<', threshold)
            return
        elif len(df_5[(df_5['ROE(%)']<5)])>0:
            print('ROE(%)<', 5)
            return
    lowest_est = 0
    highest_est = 0
    min_avg = 0
    max_avg = 0
    df_y['price_low'] = 0
    df_y['price_high'] = 0
    df_y['price_avg'] = 0
    df_y['本益比_min'] = 0
    df_y['本益比_max'] = 0
    if not df_yearly is None:
        df_yearly = df_yearly.set_index('year')
        lst_y = [y for y in df_y.index if str(y) in df_yearly.index] # 要在2張表都有資料的年份
        for y in lst_y:
            df_y.at[y, 'price_low'] = int(df_yearly.loc[str(y), 'lowest'])
            df_y.at[y, 'price_high'] = int(df_yearly.loc[str(y), 'highest'])
            df_y.at[y, 'price_avg'] = int(df_yearly.loc[str(y), 'average'])
            df_y.at[y, '本益比_min'] = int(df_yearly.loc[str(y), '本益比_min'])
            df_y.at[y, '本益比_max'] = int(df_yearly.loc[str(y), '本益比_max'])

        lowest_est = df_yearly.loc[str(this_year), 'lowest_est'] 
        highest_est = df_yearly.loc[str(this_year), 'highest_est'] 
        min_avg = df_yearly.loc[str(this_year), '本益比_min_avg'] 
        max_avg = df_yearly.loc[str(this_year), '本益比_max_avg'] 

    lst_check = ['營業收入','營業收入_成長(%)', '稅後淨利','稅後淨利_成長(%)', '股東權益', 'ROE(%)', \
                 '毛利率(%)','毛利率_成長(%)', '營益率(%)', '淨利率(%)', '每股盈餘(元)', 'EPS(Y)', 'EPS(Y)_成長(%)', \
                 '現金股利(%)', 'cash','現金股利_成長(%)', \
                 'price_low', 'price_high', 'price_avg', '本益比_min', '本益比_max' ]
    df_y = df_y.sort_index()[lst_check].T
    df_y.insert(0, 'stock_id', value=stock_id)
    df_y = df_y.rename({'營業收入':'營業收入(億)', '稅後淨利':'稅後淨利(億)'})

    if stock_id in df_today.index and 2020 in df_y.columns:
        eps_rate = (df_y.loc['EPS(Y)_成長(%)', 2020] + df_y.loc['EPS(Y)_成長(%)', 2019])/2
        eps_rate_est = eps_rate * 0.8
        price = df_today.loc[stock_id, 'close']
        df_y['股價'] = price
        eps_y = df_y.loc['每股盈餘(元)', 2021] * 4 / 3
        cash_pct = df_y.loc['現金股利(%)', 2021]/100
        df_y['預估EPS(Y)'] = round(eps_y, 1)
        df_y['本益比'] = round(df_y['股價'] / eps_y , 1)
        df_y['殖利率(%)'] = round(eps_y * cash_pct / price * 100 , 1)
        df_y['盈餘成長率(%)'] = eps_rate_est
        df_y['總報酬率(%)'] = df_y['殖利率(%)'] + eps_rate_est
        df_y['總報酬本益比'] = round(df_y['總報酬率(%)'] / df_y['本益比'], 1)
        df_y['lowest_est'] = lowest_est
        df_y['highest_est'] = highest_est
        df_y['本益比_min_avg'] = min_avg
        df_y['本益比_max_avg'] = max_avg
    return df_y