#!/usr/bin/env python3
# -*- codeing = utf-8 -*-

import datetime
import requests
import json
import tushare as ts
import pandas as pd

from my_tokens.my_tokens import *


webex_room_id = "Y2lzY29zcGFyazovL3VzL1JPT00vOWQ5NGU3NjAtNTU5ZC0xMWViLWI0YTEtM2Y0NDdhYTE0MGVj"

def sendMessage(token, room_id, message):
	header = {"Authorization": "Bearer %s" % token,
			  "Content-Type": "application/json"}
	data = {"roomId": room_id,
			"text": message}
	res = requests.post("https://api.ciscospark.com/v1/messages/",
						 headers=header, data=json.dumps(data), verify=True)
	if res.status_code == 200:
		print("消息已经发送至 Webex Teams")
	else:
		print("failed with statusCode: %d" % res.status_code)
		if res.status_code == 404:
			print("please check the bot is in the room you're attempting to post to...")
		elif res.status_code == 400:
			print("please check the identifier of the room you're attempting to post to...")
		elif res.status_code == 401:
			print("please check if the access token is correct...")

#Determine the range of trade dates.
def getDays(beforeOfDay):
	today = datetime.datetime.today()
	offset = datetime.timedelta(days=-beforeOfDay)
	start_date = (today + offset).strftime('%Y%m%d')
	end_date = today.strftime('%Y%m%d')
	return start_date, end_date

start_date, end_date = getDays(45)

pro = ts.pro_api(tushare_token)

#Get the daily quotes of the indexes.
def getIndexDaily(ts_code, start_date=start_date, end_date=end_date):
	index_daily = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
	return index_daily

def getFundDaily(ts_code, start_date=start_date, end_date=end_date):
	fund_daily = pro.fund_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
	return fund_daily


#Retrieve the trade dates and the close prices only.
def getClose(df, index_name):
	df = df[['trade_date', 'close']]
	df = df.rename(columns = {'close':index_name})
	return df


#Merge and optimize the data frames of the indexes.
def mergeDf(*args):

	df_list = []

	for arg in args:
		df_list.append(arg)

	df = pd.concat(df_list, axis=1, join='outer')
	df = df.T.drop_duplicates().T
	df = df.sort_values(by='trade_date')
	df = df.tail(21)
	df = df.reset_index(drop=True)

	return df


sh50 = getClose(getIndexDaily('000016.SH'), 'SH50')
# cyb = getClose(getIndexDaily('399006.SZ'), 'CYB')
cyb50 = getClose(getIndexDaily('399673.SZ'), 'CYB50')
kc50 = getClose(getIndexDaily('000688.SH'), 'KC50')
national_debt = getClose(getFundDaily('511010.SH'), 'National Debt')

df_result = mergeDf(sh50, cyb50, kc50, national_debt)


# print()
# print('-' * 20)
# print()
# print('Index quotes of recent 20 trade days:')
# print()
# print('-' * 20)
# print()
# print(df_result)
# print()
# print('-' * 20)
# print()


#Calculate the gains of the indexes for the dedicated duration. 
def stockGains(df):	

	df_gains = pd.DataFrame(columns=['Index', 'Gains'])

	for column in df.columns[1:]:
		ts_code = column
		gains = (df[column][20] - df[column][0]) / df[column][0]
		df_new = pd.DataFrame({'Index': ts_code, 'Gains': gains}, index=[1])
		df_gains = df_gains.append(df_new, ignore_index=True)
	
	df_gains = df_gains.sort_values(by='Gains').reset_index(drop=True)
	df_gains['Gains%'] = df_gains['Gains'].apply(lambda x: '%.2f%%' % (x * 100))

	return df_gains


index_gains = stockGains(df_result)
sendMessage(token=webex_token, room_id=webex_room_id, message=index_gains.to_string(index=False))

# print()
# print('-' * 20)
# print()
# print('Index gains of recent 20 trade days:')
# print()
# print('-' * 20)
# print()
# print(index_gains)
# print()
# print('-' * 20)
# print()


#Give trade advisor.
def tradeAdvisor(df_gains):

	max_index = df_gains.iloc[-1, 0]
	max_gain = df_gains.iloc[-1, 1]
	max_percentage = df_gains.iloc[-1, 2]

	if max_gain > 0:
		# print()
		msg = 'Gains of {index} in recent 20 trade days is {gains}, so {index} is recommended.'\
			.format(index=max_index, gains=max_percentage)
		# print()
		# print('-' * 20)
		# print()
	else:
		# print()
		msg = 'Short position!'
		# print()
		# print('-' * 20)
		# print()
	return msg


advisor = tradeAdvisor(index_gains)
sendMessage(token=webex_token, room_id=webex_room_id, message=advisor)



