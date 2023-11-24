#Running on Anaconda interpreter (base)

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from alpha_vantage.fundamentaldata import FundamentalData
from stocknews import StockNews
from datetime import date, timedelta
import requests

#Initialize Dashboard
st.title("Security Analysis App")
st.write("Use this application to analyze a security and compare its performance against an index of your choice")

#initialize index dictionary
ind_dict = {"^GSPC":"S&P 500", "^DJI":"DJIA", "^IXIC":"NASDAQ"}
ind_dict_keys = tuple(ind_dict.keys())

#Initialize variables for graph and computation purposes
entCol1,entCol2,entCol3, entCol4 = st.columns(4)
with entCol1:
    ticker = st.text_input('Ticker Symbol')
with entCol2:
    start_date = st.date_input('Start Date',value = date.today()-timedelta(days = 1095))
with entCol3:
    end_date = st.date_input('End Date')
with entCol4:
    ref_index = st.selectbox("Select Reference Index: ",options=ind_dict_keys, format_func= lambda i:ind_dict[i])

#error handling to force ticker input by user
if not ticker:
    st.write('Please Enter a Ticker Symbol to return details.')
    st.write('Price details provided by yfinance libary.')
    st.stop()

#download data for ticker and reference index
data = yf.download(ticker,start_date,end_date)
ref_data = yf.download(ref_index,start_date,end_date)


#initialize graph of returns of ticker and control data, subplots support multiple Y axes for close price
fig = make_subplots(specs =[[{"secondary_y": True}]])
#add primary ticker data, secondary y false since this will be the leftmost y axis
fig.add_trace(
    go.Scatter(x=data.index, y=data['Adj Close'], name=ticker),
    secondary_y=False 
)
#add control data, secondary y true as this will be rightmost y axis
fig.add_trace(
    go.Scatter(x=ref_data.index, y=ref_data['Adj Close'], name=ind_dict[ref_index]),
    secondary_y=True
)
#add title
fig.update_layout(
    title_text='{0} Adjusted Close Price Compared to {1} Index'.format(ticker,ind_dict[ref_index])
)
#add titles for x axis and y axes
fig.update_xaxes(title_text='Date')
fig.update_yaxes(title_text='{0} Adjusted Close Price'.format(ticker), secondary_y=False)
fig.update_yaxes(title_text='{0} Adjusted Close Price'.format(ind_dict[ref_index]),secondary_y=True)

#produce chart using Streamlit function
st.plotly_chart(fig)

#initialize separation between pricing/fundamental data and valuation modelling

fundamentals, valuation = st.tabs(['Fundamental and Pricing Details', 'Stock Price Valuation'])

with fundamentals:
    #initialize tabs for drilldown
    pricing_data, fundamental_data, news =st.tabs(['Pricing Data', 'Fundamental Data', 'News'])

    with pricing_data:
        st.header('Price Details')
        st.write('Note 1: Annualization of return completed by considering day over day return, deriving the average, and adjusting for 252 trading days.') 
        st.write('Note 2: Risk adjustment conducted without including a "risk free rate." Adjustment normalizes for volatility of returns using Standard Deviation. Values above 1.0 are preferred.')
        #initialize new dataframes to hold percentage change column for ticker and control
        data_change = data
        data_change['% Change'] = (data_change['Adj Close']/data_change['Adj Close'].shift(1)-1)*100
        
        ctrl_chg = ref_data
        ctrl_chg['% Change'] = (ctrl_chg['Adj Close']/ctrl_chg['Adj Close'].shift(1)-1)*100

        #compute annualized return based on period - adjust by 252 to account for weekends and holidays
        annualized_return = round(data_change['% Change'].mean()*252,2)
        ann_ret_ctrl=round(ctrl_chg['% Change'].mean()*252,2)
        delta_ret = round(annualized_return-ann_ret_ctrl,2)

        #compute annualized standard deviation of price movement
        stdev = round(np.std(data_change['% Change']*np.sqrt(252)),2)
        stdev_ctrl = round(np.std(ctrl_chg['% Change']*np.sqrt(252)),2)
        delta_stdev=round(stdev-stdev_ctrl,2)

        #compute risk adjusted return by dividing annualized return by annualized standard deviation
        riskadj_ret=round(annualized_return/stdev,2)
        riskadj_ret_ctrl = round(ann_ret_ctrl/stdev_ctrl,2)
        delta_riskret=round(riskadj_ret-riskadj_ret_ctrl,2)
        
        col1,col2,col3=st.columns(3)

        #Print ticker key details
        with col1:
            st.subheader('{0}'.format(ticker))
            st.write('Annualized Return: ',annualized_return,'%')
            st.write('Standard Deviation: ',stdev,'%')
            st.write('Risk adjusted return: ',riskadj_ret)
        #print control key details
        with col2:
            st.subheader(ind_dict[ref_index])
            st.write('Annualized Return: ',ann_ret_ctrl,'%')
            st.write('Standard Deviation: ',stdev_ctrl,'%')
            st.write('Risk adjusted return: ',riskadj_ret_ctrl)
        
        #print delta details
        with col3:
            st.subheader('{0} vs. {1}'.format(ticker,ind_dict[ref_index]))
            st.write('Difference'.format(ticker),delta_ret,'%')
            st.write('Difference: ',delta_stdev,'%')
            st.write('Difference: ',delta_riskret)
        
        #print price data
        st.subheader('{0} Adjusted Close Price Data'.format(ticker))
        st.write(data_change)

    with fundamental_data:
        st.header('Financial Statement Data for: {0}'.format(ticker))
        with st.form('Alpha Vantage Key'):
            key = st.text_input('Alpha Vantage Key: ')
            submitted = st.form_submit_button('OK')
            
            if submitted:
                if not key:
                    st.write('Please input an Alpha Vantage Key for details to be retrieved.')
                    st.write('Sign up for a free api key at: https://www.alphavantage.co/support/#api-key')
                else:
                    fd = FundamentalData(key,output_format = 'pandas')

                    bs = fd.get_balance_sheet_annual(ticker)[0]
                    balance_sheet = bs.T[2:]
                    balance_sheet.columns=list(bs.T.iloc[0])

                    is1 = fd.get_income_statement_annual(ticker)[0]
                    income_statement = is1.T[2:]
                    income_statement.columns = list(is1.T.iloc[0])

                    cf = fd.get_cash_flow_annual(ticker)[0]
                    cash_flow = cf.T[2:]
                    cash_flow.columns = list(cf.T.iloc[0])
                    
                    st.subheader('Financial Statement Ratios for Most Recent Year End')
                    st.write('Note: Effective Tax Rate may be an expense or benefit depending on the company')
                    finCol1, finCol2, finCol3 = st.columns(3)

                    with finCol1:
                        st.subheader('Liquidity')

                        currentRatio = float(balance_sheet.iat[balance_sheet.index.get_loc('totalCurrentAssets'),0])/float(balance_sheet.iat[balance_sheet.index.get_loc('totalCurrentLiabilities'),0])
                        st.write("Current Ratio:", round(currentRatio,4))

                        acidRatio = (float(balance_sheet.iat[balance_sheet.index.get_loc('totalCurrentAssets'),0])-float(balance_sheet.iat[balance_sheet.index.get_loc('inventory'),0]))/float(balance_sheet.iat[balance_sheet.index.get_loc('totalCurrentLiabilities'),0])
                        st.write('Acid Test Ratio: ', round(acidRatio,4))

                        cashRatio = float(balance_sheet.iat[balance_sheet.index.get_loc('cashAndCashEquivalentsAtCarryingValue'),0])/float(balance_sheet.iat[balance_sheet.index.get_loc('totalCurrentLiabilities'),0])
                        st.write('Cash Ratio: ', round(cashRatio,4))

                        opCashRatio = float(cash_flow.iat[cash_flow.index.get_loc('operatingCashflow'),0])/float(balance_sheet.iat[balance_sheet.index.get_loc('totalCurrentLiabilities'),0])
                        st.write('Operating Cash Flow Ratio: ', round(opCashRatio,4))

                    with finCol2:
                        st.subheader('Leverage')

                        debtRatio = float(balance_sheet.iat[balance_sheet.index.get_loc('totalAssets'),0])/float(balance_sheet.iat[balance_sheet.index.get_loc('totalLiabilities'),0])
                        st.write('Debt Ratio: ', round(debtRatio,4))

                        debtToEquity = float(balance_sheet.iat[balance_sheet.index.get_loc('totalLiabilities'),0])/float(balance_sheet.iat[balance_sheet.index.get_loc('totalShareholderEquity'),0])
                        st.write('Debt to Equity Ratio: ', round(debtToEquity,4))

                        intCoverage = float(income_statement.iat[income_statement.index.get_loc('operatingIncome'),0])/float(income_statement.iat[income_statement.index.get_loc('interestExpense'),0])
                        st.write('Interest Coverage Ratio: ', round(intCoverage,4))

                    with finCol3:
                        st.subheader('Efficiency')

                        assetTurnover = float(income_statement.iat[income_statement.index.get_loc('totalRevenue'),0])/((float(balance_sheet.iat[balance_sheet.index.get_loc('totalAssets'),0])+ float(balance_sheet.iat[balance_sheet.index.get_loc('totalAssets'),1]))/2)
                        st.write('Asset Turnover Ratio: ', round(assetTurnover,4))

                        inventoryTurnover = float(income_statement.iat[income_statement.index.get_loc('costofGoodsAndServicesSold'),0])/((float(balance_sheet.iat[balance_sheet.index.get_loc('inventory'),0])+float(balance_sheet.iat[balance_sheet.index.get_loc('inventory'),1]))/2)
                        st.write('Inventory Turnover Ratio: ', round(inventoryTurnover,4))

                        daySalesInv = 365/inventoryTurnover
                        st.write('Days Sales in Inventory: ', round(daySalesInv,4))

                        ETR = float(income_statement.iat[income_statement.index.get_loc('incomeTaxExpense'),0])/float(income_statement.iat[income_statement.index.get_loc('incomeBeforeTax'),0]) 
                        st.write('Effective Tax Rate: ', round(ETR*100,4),'%')
                

                    #Provide Balance Sheet details
                    st.subheader('Balance Sheet')
                    st.write(balance_sheet)

                    #Provide Income Statement Details
                    st.subheader('Income Statement')
                    st.write(income_statement)

                    #Provide Statement of Cash Flow Details
                    st.subheader('Statement of Cash Flows')
                    st.write(cash_flow)

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
    
with valuation:
    st.write('Coming soon, valuation modelling of a stock')
    st.subheader('Multiples Valuation Model')
    with st.form('Please enter ticker symbols for companies to compare below.'):
        comp1=st.text_input('Ticker 1')
        comp2=st.text_input('Ticker 2')
        comp3=st.text_input('Ticker 3')

        comp_sub = st.form_submit_button('Generate Comparison')

    if comp_sub:
        val_data = yf.Ticker(ticker).info
        comp_data = []
        for i in [comp1,comp2,comp3]:
            try:
                i_data=yf.Ticker(i).info
                details={'Company':i_data['shortName'], 'Stock Price':i_data['currentPrice'], 'Earnings Per Share':i_data['trailingEps'], 'P/E Ratio':i_data['trailingPE']}
                comp_data.append(details)

            except:
                details = {'Company':"",'Stock Price':"",'Earnings Per Share':"", 'P/E Ratio':""}
                
        
        mult_val = pd.DataFrame.from_records(comp_data)
        mult_val

        avg_pe = mult_val['P/E Ratio'].mean()
        st.write('Average Price to Earnings: ',avg_pe)

        ticker_pe = pd.DataFrame({"Ticker": ticker, 'Computed Intrinsic Value': val_data['trailingEps']*avg_pe,'Earnings Per Share':val_data['trailingEps']}, index=[0])
        ticker_pe
