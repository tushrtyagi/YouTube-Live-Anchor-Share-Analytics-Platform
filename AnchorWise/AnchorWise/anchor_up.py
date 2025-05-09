import pandas as pd
import plotly.io as pio
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import requests
import json
from bs4 import BeautifulSoup as bs
from datetime import date
from datetime import timedelta
import pymysql
import re
import threading
import time
import pandas as pd
import numpy as np
from whatsapp_api_client_python import API as API

##############################################################
#           Date Range format like "Year-Month-Day"          #
##############################################################

##############################################################
#                        DB Connections                      #
##############################################################
writer = pd.ExcelWriter('Rawfile.xlsx')
connection1 = pymysql.connect(host = 'database-1.c9asogtdnypd.ap-south-1.rds.amazonaws.com', 
                            user='admin', password='SocialMkt22',
                            port = 3306, db = 'youtube_db1')
connection2 = pymysql.connect(host = 'database-1.c9asogtdnypd.ap-south-1.rds.amazonaws.com',
                            user='admin', password='SocialMkt22',
                            port = 3306, db = 'youtube_db2')
connection3 = pymysql.connect(host='database-1.c9asogtdnypd.ap-south-1.rds.amazonaws.com', 
                            password='SocialMkt22', user='admin',
                            port = 3306, db = 'youtube_db3')

today = date.today()
today = today - timedelta(days = 1)
df1 = pd.read_sql("SELECT distinct channel,video_id FROM youtube_db1.yt_live_discovery where date = '" + str(today) + "';", con=connection1)

df1 =   df1[(df1['channel'] == 'Aaj Tak') | (df1['channel'] == 'Good_News_Today') | (df1['channel'] == 'India_TV') | (df1['channel'] == 'Republic_Bharat')
       |(df1['channel'] == 'News 24') |(df1['channel'] == 'News18_India') |(df1['channel'] == 'Zee_News') |(df1['channel'] == 'TV9_Bharatvarsh') |
       (df1['channel'] == 'ABP_News') |(df1['channel'] == 'Times_Now_Navbharat')
       |(df1['channel'] == 'India_Today_TV') | (df1['channel'] == 'CNN_News18') |(df1['channel'] == 'Republic_24x7') 
       |(df1['channel'] == 'NDTV_24x7') |(df1['channel'] == 'WION')]

vide1 = tuple(df1['video_id'].to_list())

df11 = pd.read_sql("SELECT * FROM youtube_db1.yt_live_table where Video_id IN " +str(vide1) + "and date = '"+str(today)+"'"+";" ,con=connection1)
df22 = pd.read_sql("SELECT * FROM youtube_db2.yt_live_table where Video_id IN " +str(vide1) + "and date = '"+str(today)+"'"+";" ,con=connection2)
df33 = pd.read_sql("SELECT * FROM youtube_db3.yt_live_table where Video_id IN " +str(vide1) + "and date = '"+str(today)+"'"+";" ,con=connection3)

final_df_id = pd.concat([df11,df22,df33])

df11['Dt'] = (df11['Datetime'].astype(str))
df11['Dt'] = df11['Dt'].str[:-2]
df11['Dt'] = df11['Dt']+str('00')

df11['Dt_'] = (df11['Datetime'].astype(str))
df11['Dt_'] = df11['Dt_'].str[:-2]
df11['Dt_'] = df11['Dt_']+str('00')

df22['Dt'] = (df22['Datetime'].astype(str))
df22['Dt'] = df22['Dt'].str[:-2]
df22['Dt'] = df22['Dt']+str('00')

df22['Dt_'] = (df22['Datetime'].astype(str))
df22['Dt_'] = df22['Dt_'].str[:-2]
df22['Dt_'] = df22['Dt_']+str('00')

df33['Dt'] = (df33['Datetime'].astype(str))
df33['Dt'] = df33['Dt'].str[:-2]
df33['Dt'] = df33['Dt']+str('00')

df33['Dt_'] = (df33['Datetime'].astype(str))
df33['Dt_'] = df33['Dt_'].str[:-2]
df33['Dt_'] = df33['Dt_']+str('00')

print('data is loaded from db')

df  = pd.concat([df11,df33])

tmp = df

tmp["Datetime"] = pd.to_datetime(tmp.Datetime)

tmp = tmp.sort_values(by="Datetime")

tmp["Datetime_2_new"] = tmp.Datetime.apply(lambda x : str(x)[:16])

tmp = tmp.groupby(["Channel_Name", "Datetime_2_new"]).agg({"Concurrent_Viewers":"sum"}).reset_index()
tmp.rename(columns = {"Datetime_2_new":"Datetime"}, inplace = True)
tmp["Datetime"] = tmp.Datetime.apply(lambda x: str(x)+":00")

total_datetime = tmp.Datetime.unique()

final_df = pd.DataFrame()
final_df["Datetime"] = pd.Series(total_datetime)
final_df

for i in tmp.Channel_Name.unique():
    final_df = pd.merge(final_df, tmp[tmp.Channel_Name==i], how="left")
    final_df.rename(columns={"Concurrent_Viewers":i}, inplace=True)
    del final_df["Channel_Name"]


final_df.replace(np.nan,0,inplace=True)

final_df['Datetime'] = pd.to_datetime(final_df['Datetime'])
date = [d.date() for d in final_df['Datetime']]
time = [d.time() for d in final_df['Datetime']]
day = pd.to_datetime(final_df['Datetime']).dt.day_name()

final_df.insert(1,'Date',date)
final_df.insert(2,'Time',time)
final_df.insert(3,'Day',day)

final_df1 = final_df.set_index(pd.DatetimeIndex(final_df["Datetime"])).drop("Datetime",axis=1)

df3 = final_df1.resample('60T').mean().astype(int)
df3.reset_index(inplace=True)

df3['Datetime'] = pd.to_datetime(df3['Datetime'])
date = [d.date() for d in df3['Datetime']]
time = [d.time() for d in df3['Datetime']]
day = pd.to_datetime(df3['Datetime']).dt.day_name()

df3.insert(1,'Date',date)
df3.insert(2,'Time',time)
df3.insert(3,'Day',day)

df9 = final_df1[final_df1['Time'].astype(str) >= '07:00:00']
df9 = df9.resample('1440T').mean().astype(int)
df9.reset_index(inplace=True)

df4 = df3[(df3['Time'].astype(str) == '09:00:00') | (df3['Time'].astype(str) == '10:00:00') | (df3['Time'].astype(str) == '11:00:00') | (df3['Time'].astype(str) == '13:00:00') | (df3['Time'].astype(str) == '14:00:00') |
(df3['Time'].astype(str) == '16:00:00') | (df3['Time'].astype(str) == '17:00:00') | (df3['Time'].astype(str) == '18:00:00')  | (df3['Time'].astype(str) == '20:00:00') | (df3['Time'].astype(str) == '21:00:00') | (df3['Time'].astype(str) == '22:00:00')]

df3 = final_df1.resample('30T').mean().astype(int)
df3.reset_index(inplace=True)

df3['Datetime'] = pd.to_datetime(df3['Datetime'])
date = [d.date() for d in df3['Datetime']]
time = [d.time() for d in df3['Datetime']]
day = pd.to_datetime(df3['Datetime']).dt.day_name()

df3.insert(1,'Date',date)
df3.insert(2,'Time',time)
df3.insert(3,'Day',day)

df5 = df3[(df3['Time'].astype(str) == '15:00:00') | (df3['Time'].astype(str) == '15:30:00') |  (df3['Time'].astype(str) == '19:00:00') | (df3['Time'].astype(str) == '19:30:00') | (df3['Time'].astype(str) == '20:00:00') | (df3['Time'].astype(str) == '20:30:00')]


tmp = df22

tmp["Datetime"] = pd.to_datetime(tmp.Datetime)

tmp = tmp.sort_values(by="Datetime")

tmp["Datetime_2_new"] = tmp.Datetime.apply(lambda x : str(x)[:16])

tmp = tmp.groupby(["Channel_Name", "Datetime_2_new"]).agg({"Concurrent_Viewers":"sum"}).reset_index()
tmp.rename(columns = {"Datetime_2_new":"Datetime"}, inplace = True)
tmp["Datetime"] = tmp.Datetime.apply(lambda x: str(x)+":00")

total_datetime = tmp.Datetime.unique()

final_df = pd.DataFrame()
final_df["Datetime"] = pd.Series(total_datetime)
final_df

for i in tmp.Channel_Name.unique():
    final_df = pd.merge(final_df, tmp[tmp.Channel_Name==i], how="left")
    final_df.rename(columns={"Concurrent_Viewers":i}, inplace=True)
    del final_df["Channel_Name"]


final_df.replace(np.nan,0,inplace=True)

final_df['Datetime'] = pd.to_datetime(final_df['Datetime'])
date = [d.date() for d in final_df['Datetime']]
time = [d.time() for d in final_df['Datetime']]
day = pd.to_datetime(final_df['Datetime']).dt.day_name()

final_df.insert(1,'Date',date)
final_df.insert(2,'Time',time)
final_df.insert(3,'Day',day)

final_df1 = final_df.set_index(pd.DatetimeIndex(final_df["Datetime"])).drop("Datetime",axis=1)

df3 = final_df1.resample('60T').mean().astype(int)
df3.reset_index(inplace=True)

df3['Datetime'] = pd.to_datetime(df3['Datetime'])
date = [d.date() for d in df3['Datetime']]
time = [d.time() for d in df3['Datetime']]
day = pd.to_datetime(df3['Datetime']).dt.day_name()

df3.insert(1,'Date',date)
df3.insert(2,'Time',time)
df3.insert(3,'Day',day)

df11 = final_df1[final_df1['Time'].astype(str) >= '07:00:00']
df11 = df11.resample('1440T').mean().astype(int)
df11.reset_index(inplace=True)

df6 = df3[(df3['Time'].astype(str) == '07:00:00') | (df3['Time'].astype(str) == '08:00:00') | (df3['Time'].astype(str) == '09:00:00') | (df3['Time'].astype(str) == '10:00:00') | (df3['Time'].astype(str) == '11:00:00') | (df3['Time'].astype(str) == '12:00:00')|
(df3['Time'].astype(str) == '13:00:00') |  (df3['Time'].astype(str) == '15:00:00') | (df3['Time'].astype(str) == '16:00:00') | (df3['Time'].astype(str) == '17:00:00') | (df3['Time'].astype(str) == '18:00:00') | (df3['Time'].astype(str) == '19:00:00')
| (df3['Time'].astype(str) == '21:00:00') | (df3['Time'].astype(str) == '22:00:00')]

df3 = final_df1.resample('30T').mean().astype(int)
df3.reset_index(inplace=True)

df3['Datetime'] = pd.to_datetime(df3['Datetime'])
date = [d.date() for d in df3['Datetime']]
time = [d.time() for d in df3['Datetime']]
day = pd.to_datetime(df3['Datetime']).dt.day_name()

df3.insert(1,'Date',date)
df3.insert(2,'Time',time)
df3.insert(3,'Day',day)

df7 = df3[(df3['Time'].astype(str) == '14:00:00') | (df3['Time'].astype(str) == '20:00:00') |
              (df3['Time'].astype(str) == '14:30:00') | (df3['Time'].astype(str) == '20:30:00')]

#########################################################################################
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#                            Hindi ANCHOR
#########################################################################################
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

Slot_Anchor = ['Neha Batham','Arpita Arya','Neha / Arpita','Neha Batham',
            'Ashutosh Chaturvedi','Sayeed / Rajeev / Arpita / Ashutosh','Sweta Singh',
            'Gaurav Sawant','Chitra Tripathi','Anjana Om Kashyap','Chitra Tripathi',
            'Sayeed Ansari','Anjana Om Kashyap','Anjana Om Kashyap','Anjana Om Kashyap','Sudhir Chaudhary','Sweta Singh','']

df9['Datetime'],df9['Date'],df9['Time'],df9['Day'] = '','','23:59:59','' 
final_hindi  = pd.concat([df4,df5,df9])

#final_hindi.sort_values(by='Time', inplace = True)

l=[0,1,2,3,5,4,6,7,8,9,10,11,12,13] # index order
final_hindi=final_hindi[[final_hindi.columns[i] for i in l]]

df11['Datetime'],df11['Date'],df11['Time'],df11['Day'] = '','','23:59:59','' 

final_english  = pd.concat([df6,df7,df11])

l=[0,1,2,3,5,4,6,7,8] # index order
final_english=final_english[[final_english.columns[i] for i in l]]

final_hindi["Sum"] = final_hindi.sum(axis=1)
result = (final_hindi.loc[:,"Aaj Tak":"Zee_News"].div(final_hindi["Sum"], axis=0)*100).round(1).astype(str) + '%'
result.insert(0,'Time',final_hindi['Time'])
result['Slot_Anchor'] = Slot_Anchor
final_hindi['Slot_Anchor'] = Slot_Anchor
final_hindi.drop(['Datetime','Date','Day','Sum'],inplace = True,axis = 1)
final_hindi.to_excel(writer, encoding='utf-8-sig', index = False, sheet_name='1_File')
result.to_excel(writer, encoding='utf-8-sig', index = False, sheet_name='2_File')
result['Time'] = ['09:00 - 10:00',
                    '10:00 - 11:00',
                    '11:00 - 12:00',
                    '13:00 - 14:00',
                    '14:00 - 15:00',
                    '15:00 - 15:30',
                    '15:30 - 16:00',
                    '16:00 - 17:00',
                    '17:00 - 18:00',
                    '18:00 - 19:00',
                    '19:00 - 19:30',
                    '19:30 - 20:00',
                    '20:00 - 21:00',
                    '20:00 - 20:30',
                    '20:30 - 21:00',
                    '21:00 - 22:00',
                    '22:00 - 23:00',
                    '07:00 - 23:00']

final_hindi['Time'] = ['09:00 - 10:00',
                    '10:00 - 11:00',
                    '11:00 - 12:00',
                    '13:00 - 14:00',
                    '14:00 - 15:00',
                    '15:00 - 15:30',
                    '15:30 - 16:00',
                    '16:00 - 17:00',
                    '17:00 - 18:00',
                    '18:00 - 19:00',
                    '19:00 - 19:30',
                    '19:30 - 20:00',
                    '20:00 - 21:00',
                    '20:00 - 20:30',
                    '20:30 - 21:00',
                    '21:00 - 22:00',
                    '22:00 - 23:00',
                    '07:00 - 23:00']

import plotly.graph_objects as go
fig = go.Figure(data=[go.Table(
    header=dict(values=list(result.columns),
               line_color='darkslategray',
                fill_color='green',
                align=['center'],
                font=dict(color='white', size=12,family='Arial Black')),
    cells=dict(values=result.transpose().values.tolist(),
               line_color='darkslategray',
                fill_color='white',
                align=['center'],
                font=dict(color=[['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],
                ['red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','green'],
                ['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']
                ,['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']
                ,['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']
                ,['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],
                ['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],
                ['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],
                ['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']], size=14,family='Arial'),height = 25)
               )

])
fig.update_layout(title='YT Live | Primary Feeds | Market Share% on Avrg Concurrent Users | '+ str(today),title_x=0.5)
fig.update_yaxes(tickfont_family="Arial Black")
fig.update_layout(width=1920, height=1080)
fig.update_layout(legend=dict(title_font_family="Arial",
                              font=dict(size= 20)
))
fig.update_layout(
    
    title_font_color="blue",
    
)
fig.update_layout(title={'font': {'size': 30}})
pio.write_image(fig, 'MarketShare.png', width=1980, height=1080)

fig = go.Figure(data=[go.Table(
    header=dict(values=list(final_hindi.columns),
               line_color='darkslategray',
                fill_color='green',
                align=['center'],
                font=dict(color='white', size=12,family='Arial Black')),
    cells=dict(values=final_hindi.transpose().values.tolist(),
               line_color='darkslategray',
                fill_color='white',
                align=['center'],
                font=dict(color=[['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],
                ['red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','green'],
                ['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']
                ,['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']
                ,['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']
                ,['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],
                ['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],
                ['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],
                ['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']], size=14,family='Arial'),height = 25)
               )

])
fig.update_layout(title='YT Live | Primary Feeds | Avrg Concurrent Users | '+ str(today),title_x=0.5)
fig.update_yaxes(tickfont_family="Arial Black")
fig.update_layout(width=1920, height=1080)
fig.update_layout(legend=dict(title_font_family="Arial",
                              font=dict(size= 20)
))
fig.update_layout(
    
    title_font_color="blue",
    
)
fig.update_layout(title={'font': {'size': 30}})
pio.write_image(fig, 'MarketShare1.png', width=1980, height=1080)
#########################################################################################
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#                            ENGLISH ANCHOR
#########################################################################################
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

Slot_Anchor = ['Pooja Shali','Pooja Shali','Pooja Shali','Poulomi / Sneha','Poulomi / Sneha',
        'Nabila Jamal','Nabila Jamal','Nabila Jamal','Dipali Patel','Chaiti /Sneha',
        'Chaiti /Sneha','Shiv Aroor','Akshita Nandgopal','Preeti Choudhary','Rahul Kanwal',
        'Rajdeep Sardesai','Gaurav Sawant','Abha Bakaya','']

final_english["Sum"] = final_english.sum(axis=1)
result = (final_english.loc[:,"India_Today_TV":"WION"].div(final_english["Sum"], axis=0)*100).round(1).astype(str) + '%'
result.insert(0,'Time',final_english['Time'])
result.rename(columns = {'Republic_24x7':'Republic'}, inplace = True)
result['Slot_Anchor'] = Slot_Anchor
final_english['Slot_Anchor'] = Slot_Anchor
final_english.drop(['Datetime','Date','Day','Sum'],inplace = True,axis = 1)
final_english.rename(columns = {'Republic_24x7':'Republic'}, inplace = True)
final_english.to_excel(writer, encoding='utf-8-sig', index = False, sheet_name='3_File')
result.to_excel(writer, encoding='utf-8-sig', index = False, sheet_name='4_File')

result['Time'] = [  '07:00 - 08:00',
                    '08:00 - 09:00',  
                    '09:00 - 10:00',
                    '10:00 - 11:00',
                    '11:00 - 12:00',
                    '12:00 - 13:00',
                    '13:00 - 14:00',
                    '14:00 - 14:30',
                    '14:30 - 15:00',
                    '15:00 - 16:00',
                    '16:00 - 17:00',
                    '17:00 - 18:00',
                    '18:00 - 19:00',
                    '19:00 - 20:00',
                    '20:00 - 20:30',
                    '20:30 - 21:00',
                    '21:00 - 22:00',
                    '22:00 - 23:00',
                    '07:00 - 23:00']

final_english['Time'] = [  '07:00 - 08:00',
                    '08:00 - 09:00',  
                    '09:00 - 10:00',
                    '10:00 - 11:00',
                    '11:00 - 12:00',
                    '12:00 - 13:00',
                    '13:00 - 14:00',
                    '14:00 - 14:30',
                    '14:30 - 15:00',
                    '15:00 - 16:00',
                    '16:00 - 17:00',
                    '17:00 - 18:00',
                    '18:00 - 19:00',
                    '19:00 - 20:00',
                    '20:00 - 20:30',
                    '20:30 - 21:00',
                    '21:00 - 22:00',
                    '22:00 - 23:00',
                    '07:00 - 23:00']


import plotly.graph_objects as go
fig = go.Figure(data=[go.Table(
    header=dict(values=list(result.columns),
               line_color='darkslategray',
                fill_color='green',
                align=['center'],
                font=dict(color='white', size=18,family='Arial Black')),
    cells=dict(values=result.transpose().values.tolist(),
               line_color='darkslategray',
                fill_color='white',
                align=['center'],
                font=dict(color=[['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],
                ['red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','green'],
                ['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']
                ,['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']
                ,['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']], size=14,family='Arial'),height = 25)
               )
])
fig.update_layout(title='YT Live | Primary Feeds | Market Share% on Avrg Concurrent Users |  '+ str(today),title_x=0.5)
fig.update_yaxes(tickfont_family="Arial Black")
fig.update_layout(width=1920, height=1080)
fig.update_layout(legend=dict(title_font_family="Arial",
                              font=dict(size= 20)
))
fig.update_layout(
    
    title_font_color="blue",
    
)
fig.update_layout(title={'font': {'size': 30}})
pio.write_image(fig, 'MarketShare3.png', width=1980, height=1080)

fig = go.Figure(data=[go.Table(
    header=dict(values=list(final_english.columns),
               line_color='darkslategray',
                fill_color='green',
                align=['center'],
                font=dict(color='white', size=18,family='Arial Black')),
    cells=dict(values=final_english.transpose().values.tolist(),
               line_color='darkslategray',
                fill_color='white',
                align=['center'],
               font=dict(color=[['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue'],
                ['red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','red','green'],
                ['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']
                ,['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']
                ,['black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','black','blue']], size=14,family='Arial'),height = 25)
               )

])


fig.update_layout(title='YT Live | Primary Feeds | Avrg Concurrent Users | '+ str(today),title_x=0.5)
fig.update_yaxes(tickfont_family="Arial Black")
fig.update_layout(width=1920, height=1080)
fig.update_layout(legend=dict(title_font_family="Arial",
                              font=dict(size= 20)
))
fig.update_layout(
    
    title_font_color="blue",
    
)
fig.update_layout(title={'font': {'size': 30}})
pio.write_image(fig, 'MarketShare4.png', width=1980, height=1080)

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#!                  Image Crop
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
import cv2
import numpy as np
images = ['MarketShare.png','MarketShare1.png']
img1 = cv2.imread(images[0])
img2 = cv2.imread(images[1])
y=0
x=10
h=1920
w=690
crop_image = img1[x:w, y:h]
crop_image1 = img2[x:w, y:h]
combined_image = cv2.vconcat([crop_image, crop_image1])
cv2.imwrite("Combined_hindi.png", combined_image)


import cv2
import numpy as np
images = ['MarketShare3.png','MarketShare4.png']
img1 = cv2.imread(images[0])
img2 = cv2.imread(images[1])
y=0
x=10
h=1920
w=705
crop_image = img1[x:w, y:h]
crop_image1 = img2[x:w, y:h]
combined_image = cv2.vconcat([crop_image, crop_image1])
cv2.imwrite("Combined_eng.png", combined_image)

writer.save()
writer.close()

from whatsapp_api_client_python import API as API

# ID_INSTANCE = '1101821601'
# API_TOKEN_INSTANCE = 'c46f6b04db1940b5b05bb603383b20e5142210606639482b95'

ID_INSTANCE = '7103959203'
API_TOKEN_INSTANCE = 'a46ef9b8ad364916a64640e5ae0d1a108fe065b556f848cdb2'

greenAPI = API.GreenApi(ID_INSTANCE, API_TOKEN_INSTANCE)

result = greenAPI.sending.sendFileByUpload('120363159834509194@g.us',
    "Combined_eng.png",
    'Combined_eng.png', "YT Anchor Wise Reports | Avg Concurrent Users | Market Share % | English News Channels | " + str(today))
print(result.data)

result = greenAPI.sending.sendFileByUpload('120363159834509194@g.us',
    "Combined_hindi.png",
    'Combined_hindi.png', "YT Anchor Wise Reports | Avg Concurrent Users | Market Share % | Hindi News Channels | " + str(today))
print(result.data)

result = greenAPI.sending.sendFileByUpload('120363136416495516@g.us',
    "Combined_eng.png",
    'Combined_eng.png', "YT Anchor Wise Reports | Avg Concurrent Users | Market Share % | English News Channels | " + str(today))
print(result.data)

result = greenAPI.sending.sendFileByUpload('120363136416495516@g.us',
    "Combined_hindi.png",
    'Combined_hindi.png', "YT Anchor Wise Reports | Avg Concurrent Users | Market Share % | Hindi News Channels | " + str(today))
print(result.data)
















import pandas as pd
import plotly.io as pio
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import requests
import json
from bs4 import BeautifulSoup as bs
from datetime import date
from datetime import timedelta
import pymysql
import re
import threading
import time
import pandas as pd
import numpy as np
from whatsapp_api_client_python import API as API

##############################################################
#           Date Range format like "Year-Month-Day"          #
##############################################################

##############################################################
#                        DB Connections                      #
##############################################################
writer = pd.ExcelWriter('Rawfile.xlsx')
connection1 = pymysql.connect(host = 'database-1.c9asogtdnypd.ap-south-1.rds.amazonaws.com', 
                            user='admin', password='SocialMkt22',
                            port = 3306, db = 'youtube_db1')
connection2 = pymysql.connect(host = 'database-1.c9asogtdnypd.ap-south-1.rds.amazonaws.com',
                            user='admin', password='SocialMkt22',
                            port = 3306, db = 'youtube_db2')
connection3 = pymysql.connect(host='database-1.c9asogtdnypd.ap-south-1.rds.amazonaws.com', 
                            password='SocialMkt22', user='admin',
                            port = 3306, db = 'youtube_db3')

today = date.today()
today = today - timedelta(days = 1)
df1 = pd.read_sql("SELECT distinct channel,video_id FROM youtube_db1.yt_live_discovery where date = '" + str(today) + "';", con=connection1)

df1 =   df1[(df1['channel'] == 'Aaj Tak') | (df1['channel'] == 'Good_News_Today') | (df1['channel'] == 'India_TV') | (df1['channel'] == 'Republic_Bharat')
       |(df1['channel'] == 'News 24') |(df1['channel'] == 'News18_India') |(df1['channel'] == 'Zee_News') |(df1['channel'] == 'TV9_Bharatvarsh') |
       (df1['channel'] == 'ABP_News') |(df1['channel'] == 'Times_Now_Navbharat')
       |(df1['channel'] == 'India_Today_TV') | (df1['channel'] == 'CNN_News18') |(df1['channel'] == 'Republic_24x7') 
       |(df1['channel'] == 'NDTV_24x7') |(df1['channel'] == 'WION')]

vide1 = tuple(df1['video_id'].to_list())

df11 = pd.read_sql("SELECT * FROM youtube_db1.yt_live_table where Video_id IN " +str(vide1) + "and date = '"+str(today)+"'"+";" ,con=connection1)
df22 = pd.read_sql("SELECT * FROM youtube_db2.yt_live_table where Video_id IN " +str(vide1) + "and date = '"+str(today)+"'"+";" ,con=connection2)
df33 = pd.read_sql("SELECT * FROM youtube_db3.yt_live_table where Video_id IN " +str(vide1) + "and date = '"+str(today)+"'"+";" ,con=connection3)

final_df_id = pd.concat([df11,df22,df33])

df11['Dt'] = (df11['Datetime'].astype(str))
df11['Dt'] = df11['Dt'].str[:-2]
df11['Dt'] = df11['Dt']+str('00')

df11['Dt_'] = (df11['Datetime'].astype(str))
df11['Dt_'] = df11['Dt_'].str[:-2]
df11['Dt_'] = df11['Dt_']+str('00')

df22['Dt'] = (df22['Datetime'].astype(str))
df22['Dt'] = df22['Dt'].str[:-2]
df22['Dt'] = df22['Dt']+str('00')

df22['Dt_'] = (df22['Datetime'].astype(str))
df22['Dt_'] = df22['Dt_'].str[:-2]
df22['Dt_'] = df22['Dt_']+str('00')

df33['Dt'] = (df33['Datetime'].astype(str))
df33['Dt'] = df33['Dt'].str[:-2]
df33['Dt'] = df33['Dt']+str('00')

df33['Dt_'] = (df33['Datetime'].astype(str))
df33['Dt_'] = df33['Dt_'].str[:-2]
df33['Dt_'] = df33['Dt_']+str('00')

print('data is loaded from db')

df  = pd.concat([df11,df33])

tmp = df

tmp["Datetime"] = pd.to_datetime(tmp.Datetime)

tmp = tmp.sort_values(by="Datetime")

tmp["Datetime_2_new"] = tmp.Datetime.apply(lambda x : str(x)[:16])

tmp = tmp.groupby(["Channel_Name", "Datetime_2_new"]).agg({"Concurrent_Viewers":"sum"}).reset_index()
tmp.rename(columns = {"Datetime_2_new":"Datetime"}, inplace = True)
tmp["Datetime"] = tmp.Datetime.apply(lambda x: str(x)+":00")

total_datetime = tmp.Datetime.unique()

final_df = pd.DataFrame()
final_df["Datetime"] = pd.Series(total_datetime)
final_df

for i in tmp.Channel_Name.unique():
    final_df = pd.merge(final_df, tmp[tmp.Channel_Name==i], how="left")
    final_df.rename(columns={"Concurrent_Viewers":i}, inplace=True)
    del final_df["Channel_Name"]


final_df.replace(np.nan,0,inplace=True)

final_df['Datetime'] = pd.to_datetime(final_df['Datetime'])
date = [d.date() for d in final_df['Datetime']]
time = [d.time() for d in final_df['Datetime']]
day = pd.to_datetime(final_df['Datetime']).dt.day_name()

final_df.insert(1,'Date',date)
final_df.insert(2,'Time',time)
final_df.insert(3,'Day',day)

final_df1 = final_df.set_index(pd.DatetimeIndex(final_df["Datetime"])).drop("Datetime",axis=1)

df3 = final_df1.resample('60T').mean().astype(int)
df3.reset_index(inplace=True)

df3['Datetime'] = pd.to_datetime(df3['Datetime'])
date = [d.date() for d in df3['Datetime']]
time = [d.time() for d in df3['Datetime']]
day = pd.to_datetime(df3['Datetime']).dt.day_name()

df3.insert(1,'Date',date)
df3.insert(2,'Time',time)
df3.insert(3,'Day',day)

df4 = df3[(df3['Time'].astype(str) == '09:00:00') | (df3['Time'].astype(str) == '10:00:00') | (df3['Time'].astype(str) == '11:00:00') | (df3['Time'].astype(str) == '13:00:00') | (df3['Time'].astype(str) == '14:00:00') | (df3['Time'].astype(str) == '15:00:00')|
(df3['Time'].astype(str) == '16:00:00') | (df3['Time'].astype(str) == '17:00:00') | (df3['Time'].astype(str) == '18:00:00') | (df3['Time'].astype(str) == '19:00:00') | (df3['Time'].astype(str) == '20:00:00') | (df3['Time'].astype(str) == '21:00:00') | (df3['Time'].astype(str) == '22:00:00')]

df3 = final_df1.resample('30T').mean().astype(int)
df3.reset_index(inplace=True)

df3['Datetime'] = pd.to_datetime(df3['Datetime'])
date = [d.date() for d in df3['Datetime']]
time = [d.time() for d in df3['Datetime']]
day = pd.to_datetime(df3['Datetime']).dt.day_name()

df3.insert(1,'Date',date)
df3.insert(2,'Time',time)
df3.insert(3,'Day',day)

df5 = df3[(df3['Time'].astype(str) == '15:30:00') | (df3['Time'].astype(str) == '19:30:00')]


tmp = df22

tmp["Datetime"] = pd.to_datetime(tmp.Datetime)

tmp = tmp.sort_values(by="Datetime")

tmp["Datetime_2_new"] = tmp.Datetime.apply(lambda x : str(x)[:16])

tmp = tmp.groupby(["Channel_Name", "Datetime_2_new"]).agg({"Concurrent_Viewers":"sum"}).reset_index()
tmp.rename(columns = {"Datetime_2_new":"Datetime"}, inplace = True)
tmp["Datetime"] = tmp.Datetime.apply(lambda x: str(x)+":00")

total_datetime = tmp.Datetime.unique()

final_df = pd.DataFrame()
final_df["Datetime"] = pd.Series(total_datetime)
final_df

for i in tmp.Channel_Name.unique():
    final_df = pd.merge(final_df, tmp[tmp.Channel_Name==i], how="left")
    final_df.rename(columns={"Concurrent_Viewers":i}, inplace=True)
    del final_df["Channel_Name"]


final_df.replace(np.nan,0,inplace=True)

final_df['Datetime'] = pd.to_datetime(final_df['Datetime'])
date = [d.date() for d in final_df['Datetime']]
time = [d.time() for d in final_df['Datetime']]
day = pd.to_datetime(final_df['Datetime']).dt.day_name()

final_df.insert(1,'Date',date)
final_df.insert(2,'Time',time)
final_df.insert(3,'Day',day)

final_df1 = final_df.set_index(pd.DatetimeIndex(final_df["Datetime"])).drop("Datetime",axis=1)

df3 = final_df1.resample('60T').mean().astype(int)
df3.reset_index(inplace=True)

df3['Datetime'] = pd.to_datetime(df3['Datetime'])
date = [d.date() for d in df3['Datetime']]
time = [d.time() for d in df3['Datetime']]
day = pd.to_datetime(df3['Datetime']).dt.day_name()

df3.insert(1,'Date',date)
df3.insert(2,'Time',time)
df3.insert(3,'Day',day)

df6 = df3[(df3['Time'].astype(str) == '07:00:00') | (df3['Time'].astype(str) == '08:00:00') | (df3['Time'].astype(str) == '09:00:00') | (df3['Time'].astype(str) == '10:00:00') | (df3['Time'].astype(str) == '11:00:00') | (df3['Time'].astype(str) == '12:00:00')|
(df3['Time'].astype(str) == '13:00:00') | (df3['Time'].astype(str) == '14:00:00') | (df3['Time'].astype(str) == '15:00:00') | (df3['Time'].astype(str) == '16:00:00') | (df3['Time'].astype(str) == '17:00:00') | (df3['Time'].astype(str) == '18:00:00') | (df3['Time'].astype(str) == '19:00:00')
|(df3['Time'].astype(str) == '20:00:00') | (df3['Time'].astype(str) == '21:00:00') | (df3['Time'].astype(str) == '22:00:00')]

df3 = final_df1.resample('30T').mean().astype(int)
df3.reset_index(inplace=True)

df3['Datetime'] = pd.to_datetime(df3['Datetime'])
date = [d.date() for d in df3['Datetime']]
time = [d.time() for d in df3['Datetime']]
day = pd.to_datetime(df3['Datetime']).dt.day_name()

df3.insert(1,'Date',date)
df3.insert(2,'Time',time)
df3.insert(3,'Day',day)

df7 = df3[(df3['Time'].astype(str) == '14:30:00') | (df3['Time'].astype(str) == '22:30:00')]

#########################################################################################
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#                            Hindi ANCHOR
#########################################################################################
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

Slot_Anchor = ['Neha Batham','Arpita Arya','Neha / Arpita','Neha Batham',
            'Ashutosh Chaturvedi','Sayeed / Rajeev / Arpita / Ashutosh','Sweta Singh',
            'Gaurav Sawant','Chitra Tripathi','Anjana Om Kashyap','Chitra Tripathi',
            'Sayeed Ansari','Anjana Om Kashyap','Sudhir Chaudhary','Sweta Singh']

final_hindi  = pd.concat([df4,df5])
final_hindi.sort_values(by='Time', inplace = True)

l=[0,1,2,3,5,4,6,7,8,9,10,11,12,13] # index order
final_hindi=final_hindi[[final_hindi.columns[i] for i in l]]

final_english  = pd.concat([df6,df7])
final_english.sort_values(by='Time', inplace = True)

l=[0,1,2,3,5,4,6,7,8] # index order
final_english=final_english[[final_english.columns[i] for i in l]]

final_hindi["Sum"] = final_hindi.sum(axis=1)
result = (final_hindi.loc[:,"Aaj Tak":"Zee_News"].div(final_hindi["Sum"], axis=0)*100).round(1).astype(str) + '%'
result.insert(0,'Time',final_hindi['Time'])
result['Slot_Anchor'] = Slot_Anchor
final_hindi['Slot_Anchor'] = Slot_Anchor
final_hindi.drop(['Datetime','Date','Day','Sum'],inplace = True,axis = 1)
final_hindi.to_excel(writer, encoding='utf-8-sig', index = False, sheet_name='1_File')
result.to_excel(writer, encoding='utf-8-sig', index = False, sheet_name='2_File')

import plotly.graph_objects as go
fig = go.Figure(data=[go.Table(
    header=dict(values=list(result.columns),
               line_color='darkslategray',
                fill_color='green',
                align=['center'],
                font=dict(color='white', size=12,family='Arial Black')),
    cells=dict(values=result.transpose().values.tolist(),
               line_color='darkslategray',
                fill_color='white',
                align=['center'],
                font=dict(color=['black','red','black'], size=14,family='Arial'),height=25)
               )

])
fig.update_layout(title='YT Live | Primary Feeds | Market Share% on Avrg Concurrent Users | '+ str(today),title_x=0.5)
fig.update_yaxes(tickfont_family="Arial Black")
fig.update_layout(width=1920, height=1080)
fig.update_layout(legend=dict(title_font_family="Arial",
                              font=dict(size= 20)
))
fig.update_layout(
    
    title_font_color="blue",
    
)
fig.update_layout(title={'font': {'size': 30}})
pio.write_image(fig, 'MarketShare.png', width=1980, height=1080)

fig = go.Figure(data=[go.Table(
    header=dict(values=list(final_hindi.columns),
               line_color='darkslategray',
                fill_color='green',
                align=['center'],
                font=dict(color='white', size=12,family='Arial Black')),
    cells=dict(values=final_hindi.transpose().values.tolist(),
               line_color='darkslategray',
                fill_color='white',
                align=['center'],
                font=dict(color=['black','red','black'], size=14,family='Arial'),height = 25)
               )

])
fig.update_layout(title='YT Live | Primary Feeds | Avrg Concurrent Users | '+ str(today),title_x=0.5)
fig.update_yaxes(tickfont_family="Arial Black")
fig.update_layout(width=1920, height=1080)
fig.update_layout(legend=dict(title_font_family="Arial",
                              font=dict(size= 20)
))
fig.update_layout(
    
    title_font_color="blue",
    
)
fig.update_layout(title={'font': {'size': 30}})
pio.write_image(fig, 'MarketShare1.png', width=1980, height=1080)
#########################################################################################
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#                            ENGLISH ANCHOR
#########################################################################################
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

Slot_Anchor = ['Pooja Shali','Pooja Shali','Pooja Shali','Poulomi / Sneha','Poulomi / Sneha',
        'Nabila Jamal','Nabila Jamal','Nabila Jamal','Dipali Patel','Chaiti /Sneha',
        'Chaiti /Sneha','Shiv Aroor','Akshita Nandgopal','Preeti Choudhary','Rahul Kanwal',
        'Rajdeep Sardesai','Gaurav Sawant','Abha Bakaya']

final_english["Sum"] = final_english.sum(axis=1)
result = (final_english.loc[:,"India_Today_TV":"WION"].div(final_english["Sum"], axis=0)*100).round(1).astype(str) + '%'
result.insert(0,'Time',final_english['Time'])
result.rename(columns = {'Republic_24x7':'Republic'}, inplace = True)
result['Slot_Anchor'] = Slot_Anchor
final_english['Slot_Anchor'] = Slot_Anchor
final_english.drop(['Datetime','Date','Day','Sum'],inplace = True,axis = 1)
final_english.rename(columns = {'Republic_24x7':'Republic'}, inplace = True)
final_english.to_excel(writer, encoding='utf-8-sig', index = False, sheet_name='3_File')
result.to_excel(writer, encoding='utf-8-sig', index = False, sheet_name='4_File')

import plotly.graph_objects as go
fig = go.Figure(data=[go.Table(
    header=dict(values=list(result.columns),
               line_color='darkslategray',
                fill_color='green',
                align=['center'],
                font=dict(color='white', size=18,family='Arial Black')),
    cells=dict(values=result.transpose().values.tolist(),
               line_color='darkslategray',
                fill_color='white',
                align=['center'],
                font=dict(color=['black','red','black'], size=14,family='Arial'),height = 25)
               )

])
fig.update_layout(title='YT Live | Primary Feeds | Market Share% on Avrg Concurrent Users |  '+ str(today),title_x=0.5)
fig.update_yaxes(tickfont_family="Arial Black")
fig.update_layout(width=1920, height=1080)
fig.update_layout(legend=dict(title_font_family="Arial",
                              font=dict(size= 20)
))
fig.update_layout(
    
    title_font_color="blue",
    
)
fig.update_layout(title={'font': {'size': 30}})
pio.write_image(fig, 'MarketShare3.png', width=1980, height=1080)

fig = go.Figure(data=[go.Table(
    header=dict(values=list(final_english.columns),
               line_color='darkslategray',
                fill_color='green',
                align=['center'],
                font=dict(color='white', size=18,family='Arial Black')),
    cells=dict(values=final_english.transpose().values.tolist(),
               line_color='darkslategray',
                fill_color='white',
                align=['center'],
                font=dict(color=['black','red','black'], size=14,family='Arial'),height = 25)
               )

])
fig.update_layout(title='YT Live | Primary Feeds | Avrg Concurrent Users | '+ str(today),title_x=0.5)
fig.update_yaxes(tickfont_family="Arial Black")
fig.update_layout(width=1920, height=1080)
fig.update_layout(legend=dict(title_font_family="Arial",
                              font=dict(size= 20)
))
fig.update_layout(
    
    title_font_color="blue",
    
)
fig.update_layout(title={'font': {'size': 30}})
pio.write_image(fig, 'MarketShare4.png', width=1980, height=1080)

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
#!                  Image Crop
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
import cv2
import numpy as np
images = ['MarketShare.png','MarketShare1.png']
img1 = cv2.imread(images[0])
img2 = cv2.imread(images[1])
y=0
x=10
h=1920
w=580
crop_image = img1[x:w, y:h]
crop_image1 = img2[x:w, y:h]
combined_image = cv2.vconcat([crop_image, crop_image1])
cv2.imwrite("Combined_hindi.png", combined_image)


import cv2
import numpy as np
images = ['MarketShare3.png','MarketShare4.png']
img1 = cv2.imread(images[0])
img2 = cv2.imread(images[1])
y=0
x=10
h=1920
w=590
crop_image = img1[x:w, y:h]
crop_image1 = img2[x:w, y:h]
combined_image = cv2.vconcat([crop_image, crop_image1])
cv2.imwrite("Combined_eng.png", combined_image)

writer.save()
writer.close()

from whatsapp_api_client_python import API as API

# ID_INSTANCE = '1101821601'
# API_TOKEN_INSTANCE = 'e100a5aec45f405cbcabd76e83060a92b04d11dd83d0476e9a'

ID_INSTANCE = '7103959203'
API_TOKEN_INSTANCE = 'a46ef9b8ad364916a64640e5ae0d1a108fe065b556f848cdb2'


greenAPI = API.GreenApi(ID_INSTANCE, API_TOKEN_INSTANCE)

result = greenAPI.sending.sendFileByUpload('120363159834509194@g.us',
    "Combined_eng.png",
    'Combined_eng.png', "YT Anchor Wise Reports | Avg Concurrent Users | Market Share % | English News Channels | " + str(today))
print(result.data)

result = greenAPI.sending.sendFileByUpload('120363159834509194@g.us',
    "Combined_hindi.png",
    'Combined_hindi.png', "YT Anchor Wise Reports | Avg Concurrent Users | Market Share % | Hindi News Channels | " + str(today))
print(result.data)

result = greenAPI.sending.sendFileByUpload('120363136416495516@g.us',
    "Combined_eng.png",
    'Combined_eng.png', "YT Anchor Wise Reports | Avg Concurrent Users | Market Share % | English News Channels | " + str(today))
print(result.data)

result = greenAPI.sending.sendFileByUpload('120363136416495516@g.us',
    "Combined_hindi.png",
    'Combined_hindi.png', "YT Anchor Wise Reports | Avg Concurrent Users | Market Share % | Hindi News Channels | " + str(today))
print(result.data)





{'created': True, 'chatId': '120363179112115004@g.us', 'groupInviteLink': 'https://chat.whatsapp.com/FDAhiDNyPyZIA9M1YAJuYM'}