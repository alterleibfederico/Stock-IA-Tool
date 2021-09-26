import pandas as pd
import json
import ta
import yfinance as yf
import streamlit as st
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from tradingview_ta import TA_Handler, Interval, Exchange

def showGraphs(DATA_GENERAL):
	dataGraph=DATA_GENERAL.tail(90)
	fig = make_subplots(rows=4, cols=1,shared_xaxes=True,subplot_titles=['MACD','RSI','Price and Bollinger', 'ADX'],row_heights=[0.4, 0.2, 0.2, 0.2])

	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['MACD'],name = "MACD", line_color= 'green'),row=1, col=1)
	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['MACD_S'],name = "Signal", line_color= 'red',line_width=0.8),row=1, col=1)
	fig.append_trace(go.Bar(x=dataGraph['Date'],y=dataGraph['MACD_H'],name = "Histogram"),row=1, col=1)
	
	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['RSI'],name = "RSI", line_color='red'),row=2, col=1)
	fig.add_hrect(y0=20, y1=70, line_width=0.2, fillcolor="blue", opacity=0.2,row=2,col=1)
	
	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['Close'],name = "Close", line_color='black'),row=3, col=1)
	fig.append_trace(go.Scatter(x=dataGraph['Date'],y=dataGraph['BollH'],fill='tonexty',mode='lines', line_color='skyblue',name = "Bollinger"),row=3, col=1)
	fig.append_trace(go.Scatter(x = dataGraph['Date'], y=dataGraph['BollL'],fill='tonexty',mode='lines',line_color='skyblue',name = "Bollinger"),row=3, col=1)	

	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['ADX'],name = "ADX", line_color='black'),row=4, col=1)
	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['ADX_Neg'],name = "DMI-", line_color='red',line_width=0.5),row=4, col=1)
	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['ADX_Pos'],name = "DMI+", line_color='green',line_width=0.5),row=4, col=1)
	
	fig.update_layout(showlegend=False)
	
	fig.update_layout(autosize=False,width=700,height=700)
	st.plotly_chart(fig, use_container_width=True)
	return
	

def showTecnicoTicker(ticker):
	STOCK = yf.Ticker(ticker)
	STOCK_INFO = STOCK.info

	st.title(STOCK_INFO['longName']) 
	st.markdown('** Sector **: ' + STOCK_INFO['sector'])
	st.markdown('** Industry **: ' + STOCK_INFO['industry'])

	DATA_GENERAL = STOCK.history(period="1y").reset_index()
	
	DATA_GENERAL['RSI'] = ta.momentum.RSIIndicator(DATA_GENERAL['Close'], 14, False).rsi()
	
	MACDObj=ta.trend.MACD(DATA_GENERAL['Close'],26,12,9,False)
	DATA_GENERAL['MACD'] =MACDObj.macd()
	DATA_GENERAL['MACD_S'] =MACDObj.macd_signal()
	DATA_GENERAL['MACD_H'] =MACDObj.macd_diff()

	BollObj=ta.volatility.BollingerBands(DATA_GENERAL['Close'],14)
	DATA_GENERAL['BollL'] = BollObj.bollinger_lband()
	DATA_GENERAL['BollH'] = BollObj.bollinger_hband()

	ADXObj = ta.trend.ADXIndicator(DATA_GENERAL['High'], DATA_GENERAL['Low'], DATA_GENERAL['Close'], 14, False)

	DATA_GENERAL['ADX']=ADXObj.adx()
	DATA_GENERAL['ADX_Neg']=ADXObj.adx_neg()
	DATA_GENERAL['ADX_Pos']=ADXObj.adx_pos()


	st.write(DATA_GENERAL.tail(1))

	showGraphs(DATA_GENERAL)
	return

def validarTickerTrendingView(symb,scree,exch):
	symbolTA = TA_Handler(
	symbol=symb,
	screener=scree,
	exchange=exch,
	interval=Interval.INTERVAL_1_DAY
	)
	
	summaryTicker=symbolTA.get_analysis().summary
	recom=summaryTicker['RECOMMENDATION']
	buy=summaryTicker['BUY']
	sell=summaryTicker['SELL']
	neutral=summaryTicker['NEUTRAL']
	allIndicators =(symbolTA.get_analysis().indicators)
	return buy,sell,neutral,allIndicators,recom

def createPie(buy,sell,neutral):
	labels = ['Buy','Sell','Neutral']
	values = [buy, sell, neutral]
	colors = ['palegreen', 'salmon', 'tan']

	fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
	fig.update_traces(hoverinfo='label+percent', marker=dict(colors=colors, line=dict(color='#000000', width=0.5)))
	st.sidebar.plotly_chart(fig, use_container_width=True)

def crearListadoTradingView():
	symbolsTV = pd.read_csv("symbolTradingView.csv")
	symbolsAll=[]

	latest_iteration = st.empty()	
	bar = st.progress(0)
	totalSymbols=(100/len(symbolsTV))
	i=0

	for i in range(len(symbolsTV)):
		bar.progress(int(totalSymbols*i))
		try:
			sName=(symbolsTV.loc[i].at["Symbol"])
			latest_iteration.text(f'Ticker {sName}')
			sMarket=(symbolsTV.loc[i].at["Market"])
			sExchange=(symbolsTV.loc[i].at["Exchange"])
			buy,sell,neutral,allIndicators,recom = validarTickerTrendingView(sName,sMarket,sExchange)
			if int(buy)>=BUY_CONDITION:
				symbolsAll.append((sName,buy,sell,neutral,recom,allIndicators))
		except:
			st.write(sName)
	latest_iteration.text(f'Completado 100%')
	df = pd.DataFrame(symbolsAll)
	df.to_csv('symbolRecomTradingView.csv')
	return

user_ADX = st.sidebar.text_input("Indicadores de compra (Maximo 27)", 18)
BUY_CONDITION = int(user_ADX)

if st.sidebar.button('Obtener datos'):
	crearListadoTradingView()

try:
	symbolsFile = pd.read_csv("symbolRecomTradingView.csv")
	symbolsOK = symbolsFile['0'].sort_values().tolist()
	ticker = st.sidebar.selectbox('Seleccionar un ticker del listado',symbolsOK)
except:
	st.write("No hay tickers que coincidan con los criterios seleccionados")

if st.sidebar.button('Recomendacion ticker seleccionado'):
	symbolsTV = pd.read_csv("symbolRecomTradingView.csv")
	i=0
	for s in symbolsOK:
		if s == ticker:
			showTecnicoTicker(symbolsTV.loc[i].iat[1])
			st.sidebar.write("TrandingViewer Recomienda = " +symbolsTV.loc[i].iat[5])		
			createPie(symbolsTV.loc[i].iat[2],symbolsTV.loc[i].iat[3],symbolsTV.loc[i].iat[4])
			data = (symbolsTV.loc[i].iat[6])
			daltaL=data.split(",")
			df = pd.DataFrame(daltaL)
			st.sidebar.write(df)
			break
		i=i+1
