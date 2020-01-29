import telegram.ext
from telegram.ext import Updater, CommandHandler
from telegram.ext import MessageHandler, Filters
import pandas as pd
import numpy as np
from binance.client import Client
import os
import matplotlib.pyplot as plt

# binance setup
binance_api_key = os.environ.get("BINANCE_KEY")
binance_api_secret = os.environ.get("BINANCE_SECRET")
client = Client(binance_api_key, binance_api_secret)

# telegram setup
telegram_token = os.environ.get("TELEGRAM_TOKEN")
updater = Updater(telegram_token, use_context=True)
bot = updater.bot
job = updater.job_queue

ma_1_interval = 7
ma_2_interval = 14

# first state
prices = []
history = []
for kline in client.get_historical_klines_generator("BTCUSDT", Client.KLINE_INTERVAL_30MINUTE, "10 hour ago UTC"):
    float_result = float(kline[4])
    prices.append(float_result)
ma_1 = sum(prices[-ma_1_interval:])/ma_1_interval    
ma_2 = sum(prices[-ma_2_interval:])/ma_2_interval 
state_temp = ma_1 > ma_2

# total wallet
markets = client.get_all_tickers()
btc_price = float(markets[11]['price'])
info = client.get_account()
wallet_btc = float(info['balances'][0]['free'])
wallet_usd = float(info['balances'][11]['free'])
wallet_all_temp = wallet_usd + wallet_btc*btc_price
wallet_init = wallet_usd + wallet_btc*btc_price
print("Total fiat correspondence: $", round(wallet_all_temp,2))

# state track & execute on change
def algo_bot (update):
    # total wallet
    markets = client.get_all_tickers()
    info = client.get_account()
    btc_price = float(markets[11]['price'])
    wallet_btc = float(info['balances'][0]['free'])
    wallet_usd = float(info['balances'][11]['free'])
    wallet_all = wallet_usd + wallet_btc*btc_price
    if 'wallet_all_temp' in locals():
        wallet_diff = wallet_all - wallet_all_temp
        trade_eff = wallet_diff/wallet_all_temp
    else:
        print("No previous trades yet.")
        wallet_diff = 0
        trade_eff = 0
    total_eff = (wallet_all - wallet_init) / wallet_init
    wallet_all_temp = wallet_all
    
    # get prices
    prices = []
    for kline in client.get_historical_klines_generator("BTCUSDT", Client.KLINE_INTERVAL_30MINUTE, "10 hour ago UTC"):
        float_result = float(kline[4])
        prices.append(float_result)
        
    ma_1 = sum(prices[-ma_1_interval:])/ma_1_interval    
    ma_2 = sum(prices[-ma_2_interval:])/ma_2_interval    
    state = ma_1 > ma_2
    balance = client.get_asset_balance(asset='BTC')
    # add \nLast trades result: {5}% \nMax Drawdown till beginning: {6}%
    if state != state_temp:
        state_temp = state
        if state:
            updater.bot.send_message(chat_id="@bebelere_balon", text= "Buying BTC! \nMoving Average {0} Days: {1} \nMoving Average {2} Days: {3} \nTotal value at transation time: {4} \nLast trade's gain: {5}% \nTotal gain: {6}".format(ma_1_interval,round(ma_1,2),ma_2_interval,round(ma_2,2),wallet_all_temp,trade_eff,total_eff))    
        else:
            updater.bot.send_message(chat_id="@bebelere_balon", 
                                     text= "Selling BTC! \nMoving Average {0} Days: {1} \nMoving Average {2} Days: {3} \nTotal value at transation time: {4} \nLast trade's gain: {5}% \nTotal gain: {6}"
                                     .format(ma_1_interval,round(ma_1,2),ma_2_interval,round(ma_2,2),wallet_all_temp, trade_eff, total_eff))
    else:
        updater.bot.send_message(chat_id="@bebelere_balon", text="No cross in BTC/USDT MA{0},MA{1}".format(ma_1_interval,ma_2_interval))
        if state:
            updater.bot.send_message(chat_id="@bebelere_balon", text="Long mode. Enjoying the ride. \nTotal value: {0} \nGain till last trade: {1}"
                                     .format(wallet_all_temp, trade_eff))
        else:
            updater.bot.send_message(chat_id="@bebelere_balon", text="Short mode. Waiting for the bulls \nTotal value: {0} \nGain till last trade: {1}"
                                     .format(wallet_all_temp, trade_eff))

updater.job_queue.run_repeating(algo_bot, 180, first=180)
updater.start_polling()
updater.idle()
                                     
                                     
                                     