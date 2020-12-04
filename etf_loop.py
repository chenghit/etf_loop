#!/usr/bin/env python3

import tushare as ts
import pandas as pd
import datetime


#Determine the range of trade dates.
def getDays(beforeOfDay):
	today = datetime.datetime.today()
	offset = datetime.timedelta(days=-beforeOfDay)
	start_date = (today + offset).strftime('%Y%m%d')
	end_date = today.strftime('%Y%m%d')
	return start_date, end_date

start_date, end_date = getDays(45)

token = ''

with open('token.txt', 'r') as f:
	token = f.readline()

pro = ts.pro_api(token)

#Get the daily quotes of the indexes.
def getIndexDaily(ts_code, start_date=start_date, end_date=end_date):
	index_daily = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
	return index_daily


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
cyb = getClose(getIndexDaily('399006.SZ'), 'CYB')
cyb50 = getClose(getIndexDaily('399673.SZ'), 'CYB50')
kc50 = getClose(getIndexDaily('000688.SH'), 'KC50')

df_result = mergeDf(sh50, cyb, cyb50, kc50)


print()
print('-' * 20)
print()
print('Index quotes of recent 20 trade days:')
print()
print('-' * 20)
print()
print(df_result)
print()
print('-' * 20)
print()


#Calculate the gains of the indexes for the dedicated duration. 
def stockGains(df):	

	df_gains = pd.DataFrame(columns=['Index', 'Gains'])

	for column in df.columns[1:]:
		ts_code = column
		gains = (df[column][20] - df[column][0]) / df[column][0]
		df_new = pd.DataFrame({'Index': ts_code, 'Gains': gains}, index=[1])
		df_gains = df_gains.append(df_new, ignore_index=True)
		df_gains = df_gains.sort_values(by='Gains').reset_index(drop=True)

	return df_gains


index_gains = stockGains(df_result)

print()
print('-' * 20)
print()
print('Index gains of recent 20 trade days:')
print()
print('-' * 20)
print()
print(index_gains)
print()
print('-' * 20)
print()


#Give trade advisor.
def tradeAdvisor(df_gains):

	max_index = df_gains.iloc[-1, 0]
	max_gain = df_gains.iloc[-1, 1]

	if max_gain >= 0:
		print()
		print('Gains of {index} in recent 20 days is {gains:.2%}, so {index} is recommanded.'\
			.format(index=max_index, gains=max_gain))
		print()
		print('-' * 20)
		print()
	else:
		print()
		print('Short position!')
		print()
		print('-' * 20)
		print()		


tradeAdvisor(index_gains)




