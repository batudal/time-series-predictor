import telegram.ext
from telegram.ext import Updater, CommandHandler
from telegram.ext import MessageHandler, Filters
import pandas as pd
import numpy as np
from binance.client import Client
import os
import matplotlib.pyplot as plt
import statistics
from binance.enums import *
from decimal import Decimal
# new_trade = trade("BINANCE_KEY","BINANCE_SECRET")
# new_trade.getHistory(symbol,interval)
# binance setup
binance_api_key = os.environ.get("BINANCE_KEY")
binance_api_secret = os.environ.get("BINANCE_SECRET")
client = Client(binance_api_key, binance_api_secret)
# telegram setup
telegram_token = os.environ.get("TELEGRAM_TOKEN")
updater = Updater(telegram_token, use_context=True)
bot = updater.bot
job = updater.job_queue
    
price_history = []
    
def setHistory (symbol, interval, start, end=None):
    global price_history
    if interval == '12h':
        interval = Client.KLINE_INTERVAL_12HOUR
    elif interval == '15m':
        interval = Client.KLINE_INTERVAL_15MINUTE
    elif interval == '1d':
        interval = Client.KLINE_INTERVAL_1DAY
    elif interval == '1h':
        interval = Client.KLINE_INTERVAL_1HOUR
    elif interval == '1m':
        interval = Client.KLINE_INTERVAL_1MINUTE
    elif interval == '1M':
        interval = Client.KLINE_INTERVAL_1MONTH
    elif interval == '1w':
        interval = Client.KLINE_INTERVAL_1WEEK
    elif interval == '2h':
        interval = Client.KLINE_INTERVAL_2HOUR
    elif interval == '30m':
        interval = Client.KLINE_INTERVAL_30MINUTE
    elif interval == '3d':
        interval = Client.KLINE_INTERVAL_3DAY
    elif interval == '3m':
        interval = Client.KLINE_INTERVAL_3MINUTE
    elif interval == '4h':
        interval = Client.KLINE_INTERVAL_4HOUR
    elif interval == '5m':
        interval = Client.KLINE_INTERVAL_5MINUTE
    elif interval == '6h':
        interval = Client.KLINE_INTERVAL_6HOUR
    elif interval == '8h':
        interval = Client.KLINE_INTERVAL_8HOUR
    else:
        return intervalError()     
    for kline in client.get_historical_klines_generator(symbol, interval, start, end):
        float_result = float(kline[4])
        price_history.append(float_result)
    return price_history

def intervalError (update):
    updater.bot.send_message(chat_id="@bebelere_balon", text="Wrong interval. \nUse 1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1w,1M")
    
class crossStrategy:
    def __init__ (self, symbol, interval, start, ma_1_interval, ma_2_interval, bollinger_interval, bollinger_limit):
        self.symbol = symbol
        self.interval = interval
        self.start = start
        self.end = None
        self.ma_1_interval = ma_1_interval
        self.ma_2_interval = ma_2_interval
        self.bollinger_interval = bollinger_interval
        self.bollinger_limit = bollinger_limit
        self.ma_1 = 0
        self.ma_2 = 0
        self.state = bool
        self.price_history = setHistory(self.symbol, self.interval, self.start, self.end)
    def addMovingAverage (self):
        if len(self.price_history) == 0:
            return print("Run getHistory to create a price_history first")
        self.ma_1 = sum(self.price_history[-self.ma_1_interval:])/self.ma_1_interval    
        self.ma_2 = sum(self.price_history[-self.ma_2_interval:])/self.ma_2_interval 
    def long (self):
        self.state = self.ma_1 > self.ma_2
        return self.state    
    def bollinger (self):
        bollinger_width = bollingerWidth(self.bollinger_interval)
        return bollinger_width > self.bollinger_limit
    def buyWithAll (self):
        balance = client.get_asset_balance(asset='USDT')
        trades = client.get_recent_trades(symbol='BTCUSDT')
        qty = (float(balance['free']))/float(trades[0]['price'])*0.998
        marketBuy(symbol, qty)
    def sellWithAll (self):
        balance = client.get_asset_balance(asset='BTC')
        qty = (float(balance['free']))*0.998
        marketSell(self.symbol, qty)

    def backTest (self):
        for kline in client.get_historical_klines_generator(self.symbol, self.interval, self.start, self.end):
            float_result = float(kline[4])
            price_history.append(float_result)
            if strategy.long() and strategy.bollinger():
                strategy.buyWithAll()
            else:
                strategy.sellWithAll()
        
    
        
    
def binanceCross (symbol, interval, ma_1_interval, ma_2_interval, start, end=None):    
    global state
    ma_1 = sum(price_history[-ma_1_interval:])/ma_1_interval    
    ma_2 = sum(price_history[-ma_2_interval:])/ma_2_interval 
    state = ma_1 > ma_2

def marketBuy (symbol, qty):
    qty = '{:0.0{}f}'.format(qty, 6)
    qty = str(Decimal('{}'.format(qty)))
    market_price = client.get_recent_trades(symbol=symbol)
    market_price = round(float(market_price[0]['price']),6)
    order = client.order_market_buy(symbol=symbol, quantity=qty)
    updater.bot.send_message(chat_id="@bebelere_balon", text= "Buying BTC @ Market Price: {0}"
                             .format(market_price))
                             
def marketSell (symbol, qty):
    qty = '{:0.0{}f}'.format(qty, 6)
    qty = str(Decimal('{}'.format(qty)))
    market_price = client.get_recent_trades(symbol=symbol)
    market_price = round(float(market_price[0]['price']),6)
    order = client.order_market_buy(symbol=symbol, quantity=qty)
    updater.bot.send_message(chat_id="@bebelere_balon", text= "Selling BTC @ Market Price: {0}"
                             .format(market_price))
    
def bollingerWidth(bollinger_interval):
    bollinger_ma_list = []
    bollinger_std_list = []    
    if len(price_history) == 0:
        print("Run getHistory to create a price_history first")
    pricesLength = len(price_history)-1
    for i in range(pricesLength, (pricesLength - bollinger_interval*2),-1):
        bollinger_sum = sum(price_history[(i-bollinger_interval):i])/bollinger_interval
        bollinger_ma_list.append(bollinger_sum)
    bollinger_std_list.append(statistics.stdev(bollinger_ma_list)) 
    bollinger_std_upper = bollinger_ma_list[-1] + (bollinger_std_list[-1])*2
    bollinger_std_lower = bollinger_ma_list[-1] - (bollinger_std_list[-1])*2
    bollinger_width = (bollinger_std_upper - bollinger_std_lower) / bollinger_ma_list[-1]
    return bollinger_width
    