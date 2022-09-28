from excellib import set_excel_color_monthly
from stocklib import get_stock_price, get_OTC_price
from finance import get_yearly, get_df_monthly, get_df_monthly_check, get_df_quarterly
from finance import get_this_quarter, get_quarter_income, get_quarter_finance, set_growth_eps
from finance import get_df_quarterly_all, get_df_yearly_all

import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

root = 'D:/Mia/Stock/'
path_quarterly = root + 'quarterly/'
path_monthly = root + 'monthly/'
path_month_finance = root + 'monthly_finance/'
path_yearly = root + 'yearly/'
path_finance = root + 'finance/'
path_trust = root + 'trust/'
folder_name = 'trust/'
s_today = datetime.now().strftime('%Y_%m_%d')
print(s_today)

# 公司發行股數
path_company_stock_num = root + 'company_list.xlsx'
path_check = path_quarterly + folder_name +'finance_quarterly_{}.xlsx'.format(s_today)

# # 取得今日股價
today = datetime.today().date() - timedelta(days=1)
this_year = today.year
this_quarter = get_this_quarter()

n = 1
if today.weekday() == 0:
    n = 3

print('今天:', today, '第', this_quarter, '季')
# 台灣證券交易所
df_today = get_stock_price(today)

# # 月報
# #### 彙總報表 (單位：千元)
# https://mops.twse.com.tw/mops/web/t21sc04_ifrs

# # 從月報 篩選出公司
# 上個月營收 > 30億
# 上個月營收成長 > 20% or 去年同季營收成長 > 20%
df_monthly_check = get_df_monthly_check(path_month_finance)
print(df_monthly_check.head(1))

lst_stock_id = ['2615', '1305']

# ==============================
#  取得觀察中公司的季報、預測EPS
# ==============================
lst_monthly_id = ['2615']
df_quarterly_all = get_df_quarterly_all()
df_yearly_all = get_df_yearly_all() # 寫入歷年EPS、本益比，估算今年股價min, max範圍
df_estimate = pd.DataFrame(columns = list(df_quarterly_all.columns)+['普通股數'])
# 取得公司發行股數
df_company_stock_num = pd.read_excel(path_company_stock_num, engine='openpyxl', dtype={'stock_id':str})
df_company_stock_num.set_index('stock_id', inplace=True)

print('觀察中公司有', len(lst_monthly_id), '筆')
for i in range(len(lst_monthly_id)):
    stock_id = lst_monthly_id[i]
    df = get_df_quarterly(stock_id)
    t_wait = np.random.randint(3,10)
    print(stock_id, ', wait ', t_wait)
    if df is None:
        print('df is None')
        continue
    if df.loc[df.index[0], '毛利率(%)'] < 20:
        print(stock_id, '：毛利率', df.loc[df.index[0], '毛利率(%)'], '< 20%，跳過')
        continue
    elif df.loc[df.index[0], '營益率(%)'] < 8:
        print(stock_id, '：營益率 < 8%，跳過')
        continue

    # 計算歷年同季的營收成長率、EPS
    df = set_growth_eps(df, df_today, stock_id)

#     將年度EPS寫到歷年excel裡
    lst_year = set(df.index.to_series().apply(lambda x:x[:4]))
    min_year = int(min(lst_year)) # 若最小年是2018 ，只能確定2019都有資料
    lst_year = [y for y in lst_year if int(y) > min_year]
    lst_EPS = [{'year':y, 'eps': df.loc[str(y)+'Q1', 'EPS(Y)']} for y in lst_year]

    df.reset_index(inplace=True)
    df = df.rename(columns={'index':'quarter'}) # reset_index後column名稱是index

    stock_name = ""
    if stock_id in df_today.index:
        stock_name = df_today.loc[stock_id, 'name']
        df_yearly = get_yearly(stock_id, lst_EPS, df['quarter'][0][:4], stock_name)    
        df_yearly_all = df_yearly_all.append(df_yearly, ignore_index=True)

    df.insert(0, 'name', value=stock_name)
    df.insert(0, 'stock_id', value=stock_id)

    df_quarterly_all = df_quarterly_all.append(df, ignore_index=True)
    time.sleep(t_wait)

    # ===============================
    # 預測EPS ( check_EPS )
    # ===============================
    df_new_quarter = get_quarter_finance(stock_id, df, this_year, this_quarter, df_company_stock_num, df_today)
    df_concat = pd.concat([df, df_new_quarter])
    df_concat.sort_values('quarter', ascending=False, inplace=True)
    df_estimate = df_estimate.append(df_concat)

# # 季報
# print('本月觀察公司筆數：', len(df_quarterly_all['stock_id'].unique()), df_quarterly_all['stock_id'].unique())
# set_excel_color_monthly(df_quarterly_all, path_quarterly + folder_name + 'finance_quarterly_{}.xlsx'.format(s_today))

# # 每年 EPS 預估股價
# set_excel_color_monthly(df_yearly_all, path_yearly + folder_name + 'finance_yearly_{}.xlsx'.format(s_today))

# 預測EPS ( check_EPS )
# df_estimate.to_excel(path_check.replace('finance_quarterly', 'estimate'), index=False)
print(df_estimate.head(2))


# ===============================
# # 取得公司歷年發放股利
# lst = ['2615']
# get_company_dividen(lst)
# ===============================