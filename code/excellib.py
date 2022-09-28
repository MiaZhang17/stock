def set_excel_color_monthly (df, path):
    import pandas as pd
    from openpyxl import load_workbook
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(path, engine='xlsxwriter')

    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name='Sheet1', index=False, encoding='utf8')
    # Get the xlsxwriter workbook and worksheet objects.
    workbook  = writer.book
    worksheet = writer.sheets['Sheet1']

    # Add a format. Light red fill with dark red text.
    format_bg_orange = workbook.add_format({'bg_color': '#FFA500'}) # 橘 ffa500,FF9933 
    format_bg_yellow = workbook.add_format({'bg_color': '#FFFFBB'}) # 黃
    format_bg_wheat = workbook.add_format({'bg_color': '#fadbb9'}) # 皮膚色、小麥色
    format_bg_red = workbook.add_format({'bg_color': '#FFC7CE'}) # 紅
    
    start_row = 0
    end_row = len(df)
    
    if 'finance_yearly' in path:
        worksheet.conditional_format(start_row, 0, end_row, 0,  # 2021 預估本益比、預估max min 股價 
                                     {'type':'cell',
                                    'criteria': '=',
                                    'value':'"2021"',
                                    'format':format_bg_wheat})
    elif 'finance_quarterly_' in path:
        worksheet.conditional_format(start_row, 3, end_row, 3,  # 營收/季 > 40億
                                     {'type':'cell',
                                    'criteria': '>',
                                    'value':40,
                                    'format':format_bg_wheat})
        worksheet.conditional_format(start_row, 14, end_row, 14,  # 母公司收入 < 60%
                                     {'type':'cell',
                                    'criteria': '<',
                                    'value':60,
                                    'format':format_bg_red})
        worksheet.conditional_format(start_row, 17, end_row, 17,  # 毛利率 > 15%
                                     {'type':'cell',
                                    'criteria': '>',
                                    'value':15,
                                    'format':format_bg_wheat})
        worksheet.conditional_format(start_row, 18, end_row, 18,  # 營益率 > 10%
                                     {'type':'cell',
                                    'criteria': '>',
                                    'value':10,
                                    'format':format_bg_wheat})
        worksheet.conditional_format(start_row, 24, end_row, 24,  # 股利占EPS比例(%) > 60%
                                     {'type':'cell',
                                    'criteria': '>',
                                    'value':60,
                                    'format':format_bg_wheat})
        worksheet.conditional_format(start_row, 25, end_row, 25,  # 殖利率 > 6%
                                     {'type':'cell',
                                    'criteria': '>',
                                    'value':6,
                                    'format':format_bg_wheat})
        worksheet.conditional_format(start_row, 26, end_row, 26,  # 去年同季營收成長 >20%
                                     {'type':'cell',
                                    'criteria': '>',
                                    'value':20,
                                    'format':format_bg_wheat})
    else:
        # =================== 漲跌% ============================================
        worksheet.conditional_format(start_row, 8, end_row, 9,  # 成長>20%
                                     {'type':'cell',
                                    'criteria': '>',
                                    'value':20,
                                    'format':format_bg_wheat})
        worksheet.conditional_format(start_row, 12, end_row, 12,  # 成長>20%
                                     {'type':'cell',
                                    'criteria': '>',
                                    'value':20,
                                    'format':format_bg_wheat})
    # Close the Pandas Excel writer and output the Excel file.
    writer.save()


def set_excel_color_daily (df, path):
    import pandas as pd
    from openpyxl import load_workbook
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(path, engine='xlsxwriter')

    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name='Sheet1', index=False, encoding='utf8')
    # Get the xlsxwriter workbook and worksheet objects.
    workbook  = writer.book
    worksheet = writer.sheets['Sheet1']

    # Add a format. Light red fill with dark red text.
    format_bg_orange = workbook.add_format({'bg_color': '#FFA500'}) # 橘 ffa500,FF9933 
    format_bg_wheat = workbook.add_format({'bg_color': '#fadbb9'}) # 皮膚色、小麥色
    format_bg_red = workbook.add_format({'bg_color': '#FFC7CE'}) # 紅
    format_bg_yellow = workbook.add_format({'bg_color': '#FFFFBB'}) # 黃
    format_bg_blue = workbook.add_format({'bg_color': '#7DF9FF'}) # 藍
    format_font_red = workbook.add_format({'font_color': '#FF0000'}) # 紅
    format_font_green = workbook.add_format({'font_color': '#008000'}) # 綠
    # Set the conditional format range.
    col_close = 6  # 收盤價
    col_slope5 = 13    # 5, 10, 18日均價斜率
    col_slope18 = 15    # 5, 10, 18日均價斜率
    col_K = 16    # K值
    start_row = 0
    start_col = 6
    end_row = len(df)
    end_cold = start_col
    dic_greaterthan1 = {'type':'cell',
                    'criteria': '>',
                    'value':1,
                    'format':format_font_red}
    dic_lessthan0 = {'type':'cell',
                    'criteria': '<',
                    'value':0,
                    'format':format_font_green}

    # Apply a conditional format to the cell range.
    # ================= 五日均價、十日均價 =================================
    worksheet.conditional_format(start_row, col_close, end_row, col_close,
                                 {'type':     'formula',
                                  'criteria': '=G1<L1',
                                  'format':   format_bg_red}) # 收盤價 < 10日均價
    worksheet.conditional_format(start_row, col_close, end_row, col_close,
                                 {'type':     'formula',
                                  'criteria': '=G1<J1',
                                  'format':   format_bg_wheat}) # 收盤價 < 停損點
    # =================== K,D值 ============================================
    worksheet.conditional_format(start_row, col_K, end_row, col_K,
                                 {'type':     'formula',
                                  'criteria': '=Q1-R1>0',
                                  'format':format_font_red})

    worksheet.conditional_format(start_row, col_K, end_row, col_K,
                                 {'type':     'formula',
                                  'criteria': '=Q1-R1<0',
                                  'format':format_font_green})
    # =================== 漲跌% ============================================
    worksheet.conditional_format(start_row, 18, end_row, 18,  # 股利 > 5
                                 {'type':'cell',
                                'criteria': '>',
                                'value':5,
                                'format':format_font_red})
    worksheet.conditional_format(start_row, 19, end_row, 19,  # 本益比 PER < 8 (幾年回本)
                                 {'type':'cell',
                                'criteria': '<',
                                'value':8,
                                'format':format_font_red})
    worksheet.conditional_format(start_row, 20, end_row, 20,  # 股價淨值比 PBR < 1 (股價/公司淨值)
                                 {'type':'cell',
                                'criteria': '<',
                                'value':1,
                                'format':format_font_red})
    worksheet.conditional_format(start_row, 7, end_row, 8,
                                 dic_greaterthan1)
    worksheet.conditional_format(start_row, 7, end_row, 8,
                                 dic_lessthan0)
    # =================== 5日, 10日, 18日均價斜率 ===========================
    worksheet.conditional_format(start_row, col_slope5, end_row, col_slope18,
                                 dic_greaterthan1)
    worksheet.conditional_format(start_row, col_slope5, end_row, col_slope18,
                                 dic_lessthan0)
    # =================== 外資買賣 ============================================
    worksheet.conditional_format(start_row, 24, end_row, 25,
                                 dic_greaterthan1)
    worksheet.conditional_format(start_row, 24, end_row, 25,
                                 dic_lessthan0)

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()