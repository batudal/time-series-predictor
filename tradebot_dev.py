## START THIS SCRIPT WHEN MA'S ARE SHOWING BUY SIGNAL

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

# binance setup
binance_api_key = os.environ.get("BINANCE_KEY")
binance_api_secret = os.environ.get("BINANCE_SECRET")
client = Client(binance_api_key, binance_api_secret)

# telegram setup
telegram_token = os.environ.get("TELEGRAM_TOKEN")
updater = Updater(telegram_token, use_context=True)
bot = updater.bot
job = updater.job_queue

ma_1_interval = 5
ma_2_interval = 14
bollinger_interval = 9

# first state
prices = []
history = []
for kline in client.get_historical_klines_generator("BTCUSDT", Client.KLINE_INTERVAL_1MINUTE, "1 hour ago UTC"):
    float_result = float(kline[4])
    prices.append(float_result)
ma_1 = sum(prices[-ma_1_interval:])/ma_1_interval    
ma_2 = sum(prices[-ma_2_interval:])/ma_2_interval 
state_global = False

# total wallet
trades = client.get_recent_trades(symbol='BTCUSDT')
btc_price = float(trades[0]['price'])
balance_btc = float(client.get_asset_balance(asset='BTC')['free'])

pair = client.get_symbol_info('BTCUSDT')
minQty = float(pair['filters'][2]['minQty'])
minQty = Decimal('{}'.format(minQty))
maxQty = float(pair['filters'][2]['maxQty'])
maxQty = Decimal('{}'.format(maxQty))
stepSize = float(pair['filters'][2]['stepSize'])
stepSize = Decimal('{}'.format(stepSize))
print("min",minQty,"max",maxQty,"stepSize",stepSize)

quantity = balance_btc * 0.998
print(quantity)
quantity = float('{:0.0{}f}'.format(quantity, 6))
quantity = Decimal('{}'.format(quantity))
print(quantity)
diff = quantity - minQty
print(diff)
print("step", stepSize)
print(diff % stepSize)
if quantity > minQty and quantity < maxQty and ((quantity-minQty) % stepSize) == 0:
    quantity = str(quantity)
    print(quantity)
    #order = client.order_market_sell(symbol='BTCUSDT', quantity=quantity)
else:
    if quantity < minQty:
        print("minQty problems")
    elif quantity > maxQty:
        print("maxQty problems")
    elif ((quantity-minQty) % stepSize) == 0:
        print("stepSize problems")
        

#order = client.order_market_sell(symbol='BTCUSDT', quantity=ax)

wallet_btc = balance_btc
wallet_usd = float(client.get_asset_balance(asset='USDT')['free'])
wallet_global = wallet_usd + wallet_btc*btc_price
wallet_init = wallet_usd + wallet_btc*btc_price

tradeCount = 0

wallet_at_buy = wallet_init
wallet_at_sell = 0

print("Total fiat correspondence at script start: $", round(wallet_global,2))

# state track & execute on change
def algo_bot (update):
    # total wallet
    global wallet_global
    global state_global
    global tradeCount
    global wallet_at_buy
    global wallet_at_sell
    bollinger_ma_list = []
    bollinger_std_list = []
    bollinger_sum = 0
    
    markets = client.get_all_tickers()
    info = client.get_account()
    btc_price = float(markets[11]['price'])
    wallet_btc = float(info['balances'][0]['free'])
    wallet_usd = float(info['balances'][11]['free'])
    wallet_local = wallet_usd + wallet_btc*btc_price
    total_eff = (wallet_local - wallet_init) / wallet_init
    
    # get prices
    prices = []
    for kline in client.get_historical_klines_generator("BTCUSDT", Client.KLINE_INTERVAL_1MINUTE, "1 hour ago UTC"):
        float_result = float(kline[4])
        prices.append(float_result)
    
    pricesLength = len(prices)-1
    
    for i in range(pricesLength, (pricesLength - bollinger_interval*2),-1):
        bollinger_sum = sum(prices[(i-bollinger_interval):i])/bollinger_interval
        bollinger_ma_list.append(bollinger_sum)
        
    bollinger_std_list.append(statistics.stdev(bollinger_ma_list))
    
    print(bollinger_ma_list)
    print(bollinger_std_list)
    
    ma_1 = sum(prices[-ma_1_interval:])/ma_1_interval    
    ma_2 = sum(prices[-ma_2_interval:])/ma_2_interval    
    state = ma_1 > ma_2
       
    bollinger_std_upper = bollinger_ma_list[-1] + (bollinger_std_list[-1])*2
    bollinger_std_lower = bollinger_ma_list[-1] - (bollinger_std_list[-1])*2
    print(bollinger_std_upper, bollinger_std_lower)
    bollinger_width = (bollinger_std_upper - bollinger_std_lower) / bollinger_ma_list[-1]
    print(bollinger_width)
    
    if bollinger_width > 0.0026:
        atis_serbest = True
        print("Bollinger TRUE")
    else:
        atis_serbest = False
        print("Bollinger FALSE")
    
    print(prices[-1])
    
    # add \nLast trades result: {5}% \nMax Drawdown till beginning: {6}% - bollinger kapali
    if state != state_global:
        if state: #buy
            tradeCount = tradeCount+1
            wallet_at_buy = wallet_local
            updater.bot.send_message(chat_id="@bebelere_balon", text= "Buying BTC! \nMoving Average {0} Days: {1} \nMoving Average {2} Days: {3} \nTotal value at transation time: {4} \nTotal gain: {5}"
                                     .format(ma_1_interval,round(ma_1,2),ma_2_interval,round(ma_2,2),wallet_local,total_eff)) 
            balance = client.get_asset_balance(asset='USDT')
            trades = client.get_recent_trades(symbol='BTCUSDT')
            quantity = (float(balance['free']))/float(trades[0]['price'])*0.998
            quantity = '{:0.0{}f}'.format(quantity, 6)
            quantity = str(Decimal('{}'.format(quantity)))
            order = client.order_market_buy(symbol='BTCUSDT', quantity=quantity)
        else: #sell
            tradeCount = tradeCount+1
            wallet_at_sell = wallet_local
            win = (wallet_at_sell-wallet_at_buy)/wallet_at_buy
            updater.bot.send_message(chat_id="@bebelere_balon", 
                                     text= "Selling BTC! \nMoving Average {0} Days: {1} \nMoving Average {2} Days: {3} \nTotal value at transation time: {4} \nLast trade's gain: {5}% \nTotal gain: {6}"
                                     .format(ma_1_interval,round(ma_1,2),ma_2_interval,round(ma_2,2),wallet_local, win, total_eff))
            balance_btc = float(client.get_asset_balance(asset='BTC')['free'])
            quantity = float(info['balances'][0]['free'])*0.998
            quantity = '{:0.0{}f}'.format(quantity, 6)
            quantity = str(Decimal('{}'.format(quantity)))
            order = client.order_market_sell(symbol='BTCUSDT', quantity=quantity)

    else:
        updater.bot.send_message(chat_id="@bebelere_balon", text="No cross or low bollinger width in BTC/USDT MA{0},MA{1}".format(ma_1_interval,ma_2_interval))
        win = (wallet_local-wallet_at_buy)/wallet_at_buy
        loss = (wallet_local-wallet_at_sell)
        if state:
            updater.bot.send_message(chat_id="@bebelere_balon", text="Long mode. Enjoying the ride. \nTotal value: {0} \nGain till last trade: {1}%"
                                     .format(wallet_local, round(win,4)))
        else:
            updater.bot.send_message(chat_id="@bebelere_balon", text="Short mode. Waiting for the bulls \nTotal value: {0} \nGain till last trade: {1}"
                                     .format(wallet_local, round(loss,4)))
    state_global = state
    wallet_global = wallet_local

updater.job_queue.run_repeating(algo_bot, 60, first=60)
updater.start_polling()
updater.idle()
                                     
                                     
                                     