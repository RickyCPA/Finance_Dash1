#Running on Anaconda interpreter (base)

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from alpha_vantage.fundamentaldata import FundamentalData
from stocknews import StockNews
from datetime import date, timedelta

st.title('Stock Dashboard')
ticker = st.sidebar.text_input('Ticker')
start_date = st.sidebar.date_input('Start Date',value = date.today()-timedelta(days = 2))
end_date = st.sidebar.date_input('End Date')

if not ticker:
    st.write('Please Enter a Ticker Symbol to return details.')
    st.stop()
data = yf.download(ticker,start_date,end_date)

fig = px.line(data,x=data.index,y=data['Adj Close'], title=ticker)
st.plotly_chart(fig)

pricing_data, fundamental_data, news =st.tabs(['Pricing Data', 'Fundamental Data', 'News'])

with pricing_data:
    #Write header for Pricing tab
    st.header('Price Details')
    #initialize new dataframe to hold percentage change column and print to screen
    data_change = data
    data_change['% Change'] = (data_change['Adj Close']/data_change['Adj Close'].shift(1)-1)*100
    #compute annualized return based on period - adjust by 252 to account for weekends
    annualized_return = round(data_change['% Change'].mean()*252,2)
    st.write('Annualized Return: ',annualized_return,'%')
    #compute annualized standard deviation of price movement
    stdev = round(np.std(data_change['% Change']*np.sqrt(252)),2)
    st.write('Standard Deviation is: ',stdev,'%')
    #compute risk adjusted return by dividing annualized return by annualized standard deviation
    st.write('Risk adjusted return: ',round(annualized_return/stdev,2))
    #Print Price Details Dataframe
    st.write(data_change)


with news:
    st.header(f'News for: {ticker}')
    sn = StockNews(ticker, save_news=False)
    df_news = sn.read_rss()
    for i in range(10):
        st.subheader(f'News {i+1}')
        st.write(df_news['published'][i])
        st.write(df_news['title'][i])
        st.write(df_news['summary'][i])
        title_sentiment = df_news['sentiment_title'][i]
        st.write(f'Title Sentiment {title_sentiment}')
        news_sentiment = df_news['sentiment_summary'][i]
        st.write(f'News Sentiment {news_sentiment}')

with fundamental_data:
    key = st.text_input('Alpha Vantage Key: ')
    if not key:
        st.write('Please input an Alpha Vantage Key for details to be retrieved.')
        st.stop()
    fd = FundamentalData(key,output_format = 'pandas')
    
    #Provide Balance Sheet details
    st.subheader('Balance Sheet')
    balance_sheet = fd.get_balance_sheet_annual(ticker)[0]
    bs = balance_sheet.T[2:]
    bs.columns = list(balance_sheet.T.iloc[0])
    st.write(bs)

    #Provide Income Statement Details
    st.subheader('Income Statement')
    income_statement = fd.get_income_statement_annual(ticker)[0]
    is1 = income_statement.T[2:]
    is1.columns = list(income_statement.T.iloc[0])
    st.write(is1)

    #Provide Statement of Cash Flow Details
    st.subheader('Statement of Cash Flows')
    cash_flow = fd.get_cash_flow_annual(ticker)[0]
    cf = cash_flow.T[2:]
    cf.columns = list(cash_flow.T.iloc[0])
    st.write(cf)
