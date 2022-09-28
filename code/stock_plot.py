import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np


root = '../'
path_check = root + 'daily_check/'


def plot_K_chart(df_stock, img_name):
    import talib
    img_name = df_stock.iloc[0,0] + img_name
    # mplfinance內建的漲/跌標記顏色是美國的版本(綠漲紅跌)，先用mplfinance中自訂圖表外觀功能mpf.make_marketcolors()將漲/跌顏色改為台灣版本(紅漲綠跌)，
    # 接著再將這個設定以mpf.make_mpf_style()功能保存為自訂的外觀。
    mc = mpf.make_marketcolors(up='r', down='g', inherit=True)
    s  = mpf.make_mpf_style(base_mpf_style='yahoo', marketcolors=mc)

    sma_10 = talib.SMA(np.array(df_stock['close']), 10)
    sma_20 = talib.SMA(np.array(df_stock['close']), 20)
    sma_60 = talib.SMA(np.array(df_stock['close']), 60)
    
    df_stock['k'], df_stock['d'] = talib.STOCH(df_stock['high'], df_stock['low'], df_stock['close'])
    df_stock['k'].fillna(value=0, inplace=True)
    df_stock['d'].fillna(value=0, inplace=True)

    fig = plt.figure(figsize=(20, 8))
    base_x, base_y, base_w= 0, 0, 1
    ax3_h = 0.2
    ax2_h = 0.2
    ax1_h = 0.5

    ax1 = fig.add_axes([base_x, ax3_h+ax2_h, base_w, ax1_h])
    ax2 = fig.add_axes([base_x, ax3_h, base_w, ax2_h])
    ax3 = fig.add_axes([base_x, base_y, base_w, ax3_h])
    # ax3 = fig.add_axes([0,0,1,0.2])
    
    # ax.set_xticks(lst_xticks)
    # ax.set_xticklabels(df_stock.index[::10])

    mpf.plot(df_stock, type = 'candle', ax=ax1, style=s, volume=ax3)

    plt.rcParams['font.sans-serif']=['Microsoft JhengHei'] 
    ax1.plot(sma_10, label='10日均線')
    ax1.plot(sma_20, label='20日均線')
    ax1.plot(sma_60, label='季線')


    ax2.plot(df_stock['k'], label='K值')
    ax2.plot(df_stock['d'], label='D值')

    lst_xticks = range(0, len(df_stock.index), 5)
    ax3.set_xticks(lst_xticks)
    ax3.set_xticklabels(df_stock.index[::5])
    ax1.legend(loc='upper left', bbox_to_anchor=(0,1))
    ax2.legend(loc='upper left', bbox_to_anchor=(0,1))
    ax1.set_title(img_name , fontdict={'fontsize': 32, 'fontweight': 'medium'})
    plt.savefig(path_check+img_name+'.png',bbox_inches='tight')
    return fig