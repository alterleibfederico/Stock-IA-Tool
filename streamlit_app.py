import pandas as pd
import ta
import yfinance as yf
import streamlit as st
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

def showGraphs():
	dataGraph=DATA_GENERAL.tail(90)
	fig = make_subplots(rows=5, cols=1,shared_xaxes=True,subplot_titles=['MACD','RSI','Price and Bollinger', 'ADX','Chaikin Money Flow'],row_heights=[0.4, 0.1, 0.2, 0.1, 0.1])

	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['MACD'],name = "MACD", line_color= 'green'),row=1, col=1)
	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['MACD_S'],name = "Signal", line_color= 'red',line_width=0.8),row=1, col=1)
	fig.append_trace(go.Bar(x=dataGraph['Date'],y=dataGraph['MACD_H'],name = "Histogram"),row=1, col=1)
	
	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['RSI'],name = "RSI", line_color='red'),row=2, col=1)
	fig.add_hrect(y0=30, y1=70, line_width=0.2, fillcolor="blue", opacity=0.2,row=2,col=1)
	
	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['Close'],name = "Close", line_color='black'),row=3, col=1)
	fig.append_trace(go.Scatter(x=dataGraph['Date'],y=dataGraph['BollH'],fill='tonexty',mode='lines', line_color='skyblue',name = "Bollinger"),row=3, col=1)
	fig.append_trace(go.Scatter(x = dataGraph['Date'], y=dataGraph['BollL'],fill='tonexty',mode='lines',line_color='skyblue',name = "Bollinger"),row=3, col=1)	

	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['ADX'],name = "ADX", line_color='black'),row=4, col=1)
	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['ADX_Neg'],name = "DMI-", line_color='red',line_width=0.5),row=4, col=1)
	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['ADX_Pos'],name = "DMI+", line_color='green',line_width=0.5),row=4, col=1)
	
	fig.append_trace(go.Scatter(x = dataGraph['Date'],y = dataGraph['CKM'],name = "Chaikin Money Flow", line_color='brown'),row=5, col=1)
	
	fig.update_layout(showlegend=False)
	
	fig.update_layout(autosize=False,width=700,height=700)
	st.plotly_chart(fig, use_container_width=True)
	return

def updateSymbols():
	symbolsFile = pd.read_csv("allSymbols.csv")
	symbols = symbolsFile['Symbol'].sort_values().tolist()
	symbol=['Tickers Resultantes..']
	i=0
	latest_iteration = st.empty()
	bar = st.progress(0)
	totalSymbols=(100/len(symbols))

	for s in symbols:
		i=i+1
		latest_iteration.text(f'Ticker {s}')
		bar.progress(int(totalSymbols*i))
		try:
			search=yf.Ticker(s)
				
			data_search = search.history(period="max").reset_index()[["Date","Close","Volume","Low","High"]]

			rsiS= ta.momentum.RSIIndicator(data_search['Close'], window = 14, fillna= False).rsi()
			
			if int(rsiS.tail(1))<I_RSI:
				MACDObj=ta.trend.MACD(data_search['Close'],26,12,9,fillna= False)
				macd =MACDObj.macd().tail(1)
				macdSignal =MACDObj.macd_signal().tail(1)		
				
				if int(macd)>int(macdSignal):
					ADXObj=ta.trend.ADXIndicator(data_search['High'], data_search['Low'], data_search['Close'], window = 14, fillna = False)
					adxS=ADXObj.adx().tail(1)
					adxSN=ADXObj.adx_neg().tail(1)
					adxSP=ADXObj.adx_pos().tail(1)
					
					if int(adxS)>I_ADX and int(adxSP)>int(adxSN):
						symbol.append(s)
		except:
			st.write(s)
			
	df = pd.DataFrame(symbol)
	df.to_csv('symbolSelection.csv')
	return

user_ADX = st.sidebar.text_input("ADX mayor a", 25)
I_ADX = int(user_ADX)

user_RSI = st.sidebar.text_input("RSImenor a", 65)
I_RSI= int(user_RSI)


if st.sidebar.button('Recolectar Tickers'):
	updateSymbols()

symbolsFile = pd.read_csv("symbolSelection.csv")
symbolsOK = symbolsFile['0'].sort_values().tolist()
ticker = st.sidebar.selectbox('Seleccionar un ticker del listado',symbolsOK)

tickerManual = st.sidebar.text_input("Ingresar un ticker manualmente")


recomFile = pd.read_csv("symbolRecom.csv")
recomList = recomFile['0'].sort_values().tolist()
st.sidebar.selectbox('Lista de recomendaciones:',recomList)

if st.sidebar.button('Obtener recomendaciones de compra'):
	symbolsFile = pd.read_csv("allSymbols.csv")
	symbols = symbolsFile['Symbol'].sort_values().tolist()
	
	today = datetime.datetime.now()
	yesterday = today - datetime.timedelta(days=1)
	
	yesterdayStr=(str(yesterday)[0:10])
	recom=[]

	latest_iteration = st.empty()
	bar = st.progress(0)
	totalSymbols=(100/len(symbols))
	i=0

	for s in symbols:
		i=i+1
		latest_iteration.text(f'Ticker {s}')
		bar.progress(int(totalSymbols*i))
		try:
			search=yf.Ticker(s)
			buySignal = str((search.recommendations).tail(1))
			itsThere=buySignal.find("uy")
			itsThereToday=buySignal.find(yesterdayStr)
			if itsThere>-1 and itsThereToday>-1:
				recom.append(s)
		except:
			st.write(s)
	df = pd.DataFrame(recom)
	df.to_csv('symbolRecom.csv')

if st.sidebar.button('Mostrar Análisis Técnico'):
	
	if len(tickerManual)>0:
		ticker=tickerManual
	
	STOCK = yf.Ticker(ticker)
	STOCK_INFO = STOCK.info

	st.sidebar.title(STOCK_INFO['longName']) 
	st.sidebar.markdown('** Sector **: ' + STOCK_INFO['sector'])
	st.sidebar.markdown('** Industry **: ' + STOCK_INFO['industry'])
	st.sidebar.subheader('General Stock Info') 
	st.sidebar.markdown('** Market **: ' + STOCK_INFO['market'])
	st.sidebar.markdown('** Exchange **: ' + STOCK_INFO['exchange'])
	st.sidebar.markdown('** Quote Type **: ' + STOCK_INFO['quoteType'])

	DATA_GENERAL = STOCK.history(period="max").reset_index()
	
	DATA_GENERAL['RSI'] = ta.momentum.RSIIndicator(DATA_GENERAL['Close'], window = 14, fillna= False).rsi()
		
	MACDObj=ta.trend.MACD(DATA_GENERAL['Close'],26,12,9,fillna= False)
	DATA_GENERAL['MACD'] =MACDObj.macd()
	DATA_GENERAL['MACD_S'] =MACDObj.macd_signal()
	DATA_GENERAL['MACD_H'] =MACDObj.macd_diff()

	BollObj=ta.volatility.BollingerBands(DATA_GENERAL['Close'],window=14)
	DATA_GENERAL['BollL'] = BollObj.bollinger_lband()
	DATA_GENERAL['BollH'] = BollObj.bollinger_hband()

	ADXObj = ta.trend.ADXIndicator(DATA_GENERAL['High'], DATA_GENERAL['Low'], DATA_GENERAL['Close'], window = 14, fillna = False)

	DATA_GENERAL['ADX']=ADXObj.adx()
	DATA_GENERAL['ADX_Neg']=ADXObj.adx_neg()
	DATA_GENERAL['ADX_Pos']=ADXObj.adx_pos()


	DATA_GENERAL['CKM']=ta.volume.ChaikinMoneyFlowIndicator(DATA_GENERAL['High'], DATA_GENERAL['Low'], DATA_GENERAL['Close'], DATA_GENERAL['Volume'], window = 20, fillna = False).chaikin_money_flow() 

	st.write(DATA_GENERAL.tail(2))

	showGraphs()

	'''
	# Análisis Técnico
	### RSI (Momentum)
	RSI > 70 Sobrecompra /// RSI < 30 es sobreventa
	 
	### MACD (Tendencia)
	MACD > Signal ---> Alcista /// MACD < signal ---> Bajista

	### ADX (Tendencia y Fuerza)
	0-25 ---> Baja o Nula //25-50 Tendencia

	50-75 Fuerte Tendencia // 50-100 Tendencia Extrema

	+DMI > -DMI Precios en suba /// , +DMI < -DMI Precios en baja

	### Bollinger (Volatilidad)
	Precio cerca de Bollinger High Sobrecompra /// Precio cerca de Bollinger Low sobreventa

	### Chaikin Money Flow (Volumen)
	CMF cercano a 1 ---> Compra

	CMF cercano a  - 1 ---> Venta
	'''
	st.write((STOCK.recommendations).tail(1))
