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
ma_2_interval = 7
bollinger_interval = 9

# first state
prices = []
history = []
for kline in client.get_historical_klines_generator("BTCUSDT", Client.KLINE_INTERVAL_15MINUTE, "10 hour ago UTC"):
    float_result = float(kline[4])
    prices.append(float_result)
ma_1 = sum(prices[-ma_1_interval:])/ma_1_interval    
ma_2 = sum(prices[-ma_2_interval:])/ma_2_interval 
state_global = True

# total wallet
trades = client.get_recent_trades(symbol='BTCUSDT')
btc_price = float(trades[0]['price'])
balance_btc = float(client.get_asset_balance(asset='BTC')['free'])

#pair = client.get_symbol_info('BTCUSDT')
#minQty = float(pair['filters'][2]['minQty'])
#minQty = Decimal('{}'.format(minQty))
#maxQty = float(pair['filters'][2]['maxQty'])
#maxQty = Decimal('{}'.format(maxQty))
#stepSize = float(pair['filters'][2]['stepSize'])
#stepSize = Decimal('{}'.format(stepSize))
#print("min",minQty,"max",maxQty,"stepSize",stepSize)
#
#quantity = balance_btc * 0.998
#print(quantity)
#quantity = float('{:0.0{}f}'.format(quantity, 6))
#quantity = Decimal('{}'.format(quantity))
#print(quantity)
#diff = quantity - minQty
#print(diff)
#print("step", stepSize)
#print(diff % stepSize)

#if quantity > minQty and quantity < maxQty and ((quantity-minQty) % stepSize) == 0:
#    quantity = str(quantity)
#    print(quantity)
#    #order = client.order_market_sell(symbol='BTCUSDT', quantity=quantity)
#else:
#    if quantity < minQty:
#        print("minQty problems")
#    elif quantity > maxQty:
#        print("maxQty problems")
#    elif ((quantity-minQty) % stepSize) == 0:
#        print("stepSize problems")
        

#order = client.order_market_sell(symbol='BTCUSDT', quantity=ax)

wallet_btc = balance_btc
wallet_usd = float(client.get_asset_balance(asset='USDT')['free'])
wallet_global = wallet_usd/btc_price + wallet_btc
wallet_init = wallet_usd/btc_price + wallet_btc

tradeCount = 0

wallet_at_buy = wallet_init
wallet_at_sell = 0

print("Total amount in BTC at script start: {0} \nBTC amount: {1} \nUSDT amount: {2}".format(round(wallet_global,4),round(wallet_btc,4),round(wallet_usd,4)))

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
    
    trades = client.get_recent_trades(symbol='BTCUSDT')
    btc_price = float(trades[0]['price'])
    wallet_btc = float(client.get_asset_balance(asset='BTC')['free'])
    wallet_usd = float(client.get_asset_balance(asset='USDT')['free'])
    wallet_local = wallet_usd/btc_price + wallet_btc
    total_eff = (wallet_local - wallet_init) / wallet_init
    
    # get prices
    prices = []
    for kline in client.get_historical_klines_generator("BTCUSDT", Client.KLINE_INTERVAL_15MINUTE, "10 hour ago UTC"):
        float_result = float(kline[4])
        prices.append(float_result)
    
    pricesLength = len(prices)-1
    
    for i in range(pricesLength, (pricesLength - bollinger_interval*2),-1):
        bollinger_sum = sum(prices[(i-bollinger_interval):i])/bollinger_interval
        bollinger_ma_list.append(bollinger_sum)
        
    bollinger_std_list.append(statistics.stdev(bollinger_ma_list))   
    ma_1 = sum(prices[-ma_1_interval:])/ma_1_interval    
    ma_2 = sum(prices[-ma_2_interval:])/ma_2_interval    
    state = ma_1 > ma_2
       
    bollinger_std_upper = bollinger_ma_list[-1] + (bollinger_std_list[-1])*2
    bollinger_std_lower = bollinger_ma_list[-1] - (bollinger_std_list[-1])*2
    bollinger_width = (bollinger_std_upper - bollinger_std_lower) / bollinger_ma_list[-1]
    
    if bollinger_width > 0.0026:
        atis_serbest = True
    else:
        atis_serbest = False
    
    print(prices[-1])
    
    # add \nLast trades result: {5}% \nMax Drawdown till beginning: {6}% - bollinger kapali
    if state != state_global:
        if state: 
            tradeCount = tradeCount+1
            wallet_at_buy = wallet_local
            balance = client.get_asset_balance(asset='USDT')
            trades = client.get_recent_trades(symbol='BTCUSDT')
            quantity = (float(balance['free']))/float(trades[0]['price'])*0.998
            quantity = '{:0.0{}f}'.format(quantity, 6)
            quantity = str(Decimal('{}'.format(quantity)))
            latest_price = round(float(trades[0]['price']),6)
            order = client.order_market_buy(symbol='BTCUSDT', quantity=quantity)
            updater.bot.send_message(chat_id="@bebelere_balon", text= "Buying BTC @ Price: {0} \nTotal value: {1} \nTotal gain: {2}"
                                     .format(latest_price,round(wallet_local,6),round(total_eff,6))) 
            updater.bot.send_animation(chat_id="@bebelere_balon", animation="https://media.giphy.com/media/sDcfxFDozb3bO/giphy.gif")
        else:
            tradeCount = tradeCount+1
            wallet_at_sell = wallet_local
            win = (wallet_at_sell-wallet_at_buy)/wallet_at_buy
            trades = client.get_recent_trades(symbol='BTCUSDT')
            latest_price = round(float(trades[0]['price']),6)
            balance_btc = float(client.get_asset_balance(asset='BTC')['free'])*0.998
            quantity = '{:0.0{}f}'.format(balance_btc, 6)
            quantity = str(Decimal('{}'.format(quantity)))
            order = client.order_market_sell(symbol='BTCUSDT', quantity=quantity)
            updater.bot.send_message(chat_id="@bebelere_balon", 
                                     text= "Selling BTC @ {0} \nTotal value at transation time: {1} \nLast trade's gain: {2}% \nTotal gain: {3}"
                                     .format(latest_price,round(wallet_local,6), round(win,6), round(total_eff,6)))
            updater.bot.send_animation(chat_id="@bebelere_balon", animation="https://media.giphy.com/media/l2JdUrmFPxNZZiWYM/giphy.gif")


    else:
        if state:
            win = (wallet_local-wallet_at_buy)/wallet_at_buy
            updater.bot.send_message(chat_id="@bebelere_balon", text="Long mode. Enjoying the ride. \nTotal value: {0} BTC \nGain till last trade: {1}%"
                                     .format(round(wallet_local,6), round(win,2)))
        else:
            loss = (wallet_local-wallet_at_sell)
            updater.bot.send_message(chat_id="@bebelere_balon", text="Short mode. Waiting for the bulls \nTotal value: {0} BTC \nGain till last trade: {1}"
                                     .format(round(wallet_local,6), round(loss,4)))
    state_global = state
    wallet_global = wallet_local

updater.job_queue.run_repeating(algo_bot, 900, first=900)
updater.start_polling()
updater.idle()
                                     
                                     
                                     