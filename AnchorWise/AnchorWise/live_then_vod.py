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
from googleapiclient.discovery import build
from bs4 import BeautifulSoup as bs
import concurrent.futures
import requests
import pandas as pd
import json

def make_clickable(url, name):
	return '<a href="{}" rel="noopener noreferrer" target="_blank">{}</a>'.format(url,name)

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

today = date.today()

import datetime as dt
#curt = dt.datetime.now() - dt.timedelta(minutes = 0)
#curt = dt.datetime.strftime(curt, "%Y-%m-%d %H:%M:%S")
nextTime = dt.datetime.now() - dt.timedelta(minutes = 60)
next15 = dt.datetime.strftime(nextTime, "%Y-%m-%d %H:%M:%S")

df11 = pd.read_sql("SELECT distinct video_id,title,date,concurrent_viewers,channel_name  FROM youtube_db1.yt_live_table where concurrent_viewers = 1 and channel_name = 'Aaj Tak' and datetime >= '" + str(next15) +"';" ,con=connection1)
B = df11['video_id'].to_list()
A = pd.read_excel('idfinder.xlsx')['video_id'].to_list()
filters = (list(set(B).difference(A)))

df11.to_excel('idfinder.xlsx',index = False)
def duration_to_string(string) :
	string = string.replace('P', '')
	string = string.replace('T', '')
	string = str(string)
	t = 0
	i = 0
	dictionary = {'D' : 86400, 'H' : 3600, 'M' : 60, 'S' : 1}
	for j in range(len(string) - 1) :
		s = string[i : j + 1]
		if not s.isdigit() :
			t += int(string[i : j]) * dictionary[string[j]]
			i = j + 1
	t += int(string[i : len(string) - 1]) * dictionary[string[len(string) - 1]]
	return t

def convert_to_IST(date, format) :
	from datetime import datetime, timedelta
	date = datetime.strptime(date, format) + timedelta(hours = 5, minutes = 30)
	return date.strftime('%Y-%m-%d %H:%M:%S')

output = pd.DataFrame()
def main (response):
	global output 
	document = {
	
		}
	for dictionary in response :        
		try:
			try:
				document['Title'] = dictionary['snippet']['title']
				document['Title'] = re.sub('[\'\"]', '', document['Title'])
			except:
				document['Title'] = dictionary['snippet']['title']
				document['Title'] = re.sub('[\'\"]', '', document['Title'])
		except:
			document['Title'] = 'NONE'

		try:
			document['Channel_Name'] =  dictionary['snippet']['channelTitle']
			document['Channel_Name'] = re.sub('[\'\"]', '', document['Channel_Name']).replace('Republic Bharat','Republic_Bharat').replace('IndiaTV','India_TV').replace('IndiaTV News','India_TV_News').replace('The Lallantop','The_Lallantop').replace('DD News','DD_News').replace('Good News Today','Good_News_Today').replace('ABPLIVE','ABP_News_Hindi').replace('Doordarshan National','DD_National')
		except:
			document['Channel_Name'] = 'NONE'

		try:
			document['View_Count'] =  dictionary['statistics']['viewCount']
		except:
			document['View_Count'] = 'NONE'
		
		try:
			document['Video_Id'] = dictionary['id']
		except:
			document['Video_Id'] = 'NONE'
		
		try:
			document['Age_restricted'] = dictionary['contentDetails']['contentRating']['ytRating']
		except:
			document['Age_restricted'] = 'NONE'
		
		try:
			import re
			from datetime import timedelta
			def youtube_duration_to_time(duration):
				return str(timedelta(seconds=sum(int(x) * {'H': 3600, 'M': 60, 'S': 1}[y] for x, y in re.findall(r'(\d+)([HMS])', duration))))

			document['Duration'] = youtube_duration_to_time(str(dictionary['contentDetails']['duration']))
		except:
			document['Duration'] = 'NONE'
	
		if 'liveStreamingDetails' in dictionary :
	
			try:
				document['IST_published_at'] = convert_to_IST(dictionary['snippet']['publishedAt'], format='%Y-%m-%dT%H:%M:%SZ')
			except:
				document['IST_published_at'] = 'NONE'

			try:
				document['IST_actualstarttime'] = convert_to_IST(dictionary['liveStreamingDetails']['actualStartTime'], format='%Y-%m-%dT%H:%M:%SZ')
			except:
				document['IST_actualstarttime'] = 'NONE'


			try:
				document['IST_actual_endtime'] = convert_to_IST(dictionary['liveStreamingDetails']['actualEndTime'], format='%Y-%m-%dT%H:%M:%SZ')
			except:
				document['IST_actual_endtime'] = 'NONE'

			try:
				document['IST_scheduled_starttime'] = convert_to_IST(dictionary['liveStreamingDetails']['scheduledStartTime'], format='%Y-%m-%dT%H:%M:%SZ')
			except:
				document['IST_scheduled_starttime'] = 'NONE'

			document['Type'] = 'Live then VOD'

		df = pd.DataFrame([document],columns=document.keys())

		output = pd.concat([output,df], ignore_index=True)
		

def main1 ():
	global output
	try:
		start = time.time()
		n = 50
		l = filters
		x = [l[i:i + n] for i in range(0, len(l), n)]
		if len(x) >0:
			for ixd in x :
				# ids =  ','.join(ixd)
				id = (str(ixd).replace(']','').replace('[','')).strip()
				id = id.replace("'",'')
				id = id.replace(' ','')
				ids = id.strip()
				try:
					youtube = build('youtube', 'v3', 
							developerKey='AIzaSyD-JPrfMJP3zOJxNrycIbaO_6SQv4_J1t4')
					ch_request = youtube.videos().list(
							part="snippet,statistics,liveStreamingDetails,contentDetails",
							id = ids)
					response = ch_request.execute()['items']
					main(response)
				except:pass
	except:pass

main1()

if len(output) > 0 :
	print(output)
	output.to_excel('LiveThenVod.xlsx',index = False)
	output = pd.read_excel('LiveThenVod.xlsx')
	messages = [f"Message : This Video Id Is Converted Live To VOD, ID : {row['Video_Id']}, Starttime : {row['IST_actualstarttime']}, Endtime : {row['IST_actual_endtime']},Duration : {row['Duration']},Type : {row['Type']}, Link : https://www.youtube.com/watch?v={row['Video_Id']}" for _, row in output.iterrows()]
	for message in messages:
		print(message)

		from whatsapp_api_client_python import API as API

		# ID_INSTANCE = '1101821601'
		# API_TOKEN_INSTANCE = 'e100a5aec45f405cbcabd76e83060a92b04d11dd83d0476e9a'
		ID_INSTANCE = '7103959203'
		API_TOKEN_INSTANCE = 'a46ef9b8ad364916a64640e5ae0d1a108fe065b556f848cdb2'

		greenAPI = API.GreenApi(ID_INSTANCE, API_TOKEN_INSTANCE)


		result = greenAPI.sending.sendMessage('120363150741853150@g.us',str(message))














