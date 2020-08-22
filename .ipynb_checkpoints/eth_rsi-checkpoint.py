#!/usr/bin/env python3
# -*- coding: utf8 -*-

from binance.client import Client
import os
import telegram.ext
from telegram.ext import Updater, CommandHandler
from telegram.ext import MessageHandler, Filters
from decimal import Decimal

binance_api_key = os.environ.get("BINANCE_KEY")
binance_api_secret = os.environ.get("BINANCE_SECRET")
client = Client(binance_api_key, binance_api_secret)

telegram_token = os.environ.get("TELEGRAM_TOKEN")
updater = Updater(telegram_token, use_context=True)
bot = updater.bot
job = updater.job_queue

balance_usd = float(client.get_asset_balance(asset='USDT')['free'])
balance_eth = float(client.get_asset_balance(asset='ETH')['free'])

price = float(client.get_recent_trades(symbol='ETHUSDT')[0]['price'])
balance_converted = (balance_eth)*(price)

if balance_converted > balance_usd:
    updater.bot.send_message(chat_id="@bebelere_balon", 
                             text= "ETH-RSI algo is starting. \nCurrently long on ETH. \nAccount balance: {} ETH.".format(balance_eth))
    have_crypto = True
else:
    updater.bot.send_message(chat_id="@bebelere_balon", 
                             text= "ETH-RSI algo is starting. \nCurrently short on ETH. \nAccount balance: {} USDT".format(balance_usd))
    have_crypto = False

def getKlines (hours):
    history = []
    hours = (hours * 2) + 1
    for kline in client.get_historical_klines_generator("ETHUSDT", 
                                                        Client.KLINE_INTERVAL_1HOUR, 
                                                        "{} hours ago UTC".format(hours)):
        history.append(float(kline[4]))
        
    del history[-1]
    return history

def rsi (history, rollingdays):
    gain = []
    loss = []
    for i in range(len(history)):
        if  i >= rollingdays:
            if history[i] - history[i-1] > 0:
                gain.append((history[i] - history[i-1]) / history[i-1])
            else: 
                loss.append((history[i] - history[i-1]) / history[i-1])
    avg_gain = sum(gain) / rollingdays
    avg_loss = abs(sum(loss) / rollingdays)
    return avg_gain/avg_loss         
                

def buyEth ():
    balance = client.get_asset_balance(asset='USDT')['free']
    balance = float(balance)
    trades = client.get_recent_trades(symbol='ETHUSDT')
    trades = float(trades[0]['price'])              
    qty = (balance)/(trades)*0.998
    qty = '{:0.0{}f}'.format(qty, 3)
    qty = str(Decimal('{}'.format(qty)))
    order = client.order_market_buy(symbol='ETHUSDT', quantity=qty)
    
def sellEth ():
    balance = client.get_asset_balance(asset='ETH')
    qty = (float(balance['free']))*0.998
    qty = '{:0.0{}f}'.format(qty, 3)
    qty = str(Decimal('{}'.format(qty)))
    order = client.order_market_sell(symbol='ETHUSDT', quantity=qty)
    
def rsiBot (update):
    global have_crypto
    RSI_index = 100 - (100 / (1 + rsi(getKlines(24), 24)))
    if RSI_index > 60:
        if have_crypto == False:
            buyEth()
            updater.bot.send_message(chat_id="@bebelere_balon", text= "Buying ETH, RSI: {0}".format(RSI_index))
            have_crypto = True
        else:
            updater.bot.send_message(chat_id="@bebelere_balon", text= "RSI: {0} but you're already in ETH.".format(RSI_index))
    elif RSI_index < 40:
        if have_crypto:
            sellEth()
            updater.bot.send_message(chat_id="@bebelere_balon", text= "Selling ETH, RSI: {0}".format(RSI_index))
            have_crypto = False
        else:
            updater.bot.send_message(chat_id="@bebelere_balon", text= "RSI: {0} but you're already in USDT.".format(RSI_index))
    else:
        updater.bot.send_message(chat_id="@bebelere_balon", text= "No order. RSI: {0}".format(RSI_index))
#    updater.bot.send_message(chat_id="@bebelere_balon", text= "No order. RSI: {0}".format(RSI_index))


updater.job_queue.run_repeating(rsiBot, 3600, first=0)
updater.start_polling()
updater.idle()