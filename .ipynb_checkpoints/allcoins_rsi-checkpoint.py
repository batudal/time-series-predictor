#!/usr/bin/env python
# coding: utf-8

from binance.client import Client
import os
import telegram.ext
from telegram.ext import Updater, CommandHandler
from telegram.ext import MessageHandler, Filters

binance_api_key = os.environ.get("BINANCE_KEY")
binance_api_secret = os.environ.get("BINANCE_SECRET")
client = Client(binance_api_key, binance_api_secret)

telegram_token = os.environ.get("TELEGRAM_TOKEN")
updater = Updater(telegram_token, use_context=True)
bot = updater.bot
job = updater.job_queue

def getSymbols():
    xinfo = client.get_exchange_info()
    symbols = []
    for i in xinfo['symbols']:
        if "USDT" in i['symbol']:
            symbols.append(i['symbol'])
    return symbols

def getKlines (hours, symbol):
    history = []
    hours = (hours * 2) + 1
    for kline in client.get_historical_klines_generator("{}".format(symbol), 
                                                        Client.KLINE_INTERVAL_1HOUR, 
                                                        "{} hours ago UTC".format(hours)):
        history.append(float(kline[4]))
        
    if history: del history[-1]
    return history

def rsi (history, rollingdays):
    gain = []
    loss = []
    if history:
        for i in range(len(history)):
            if  i >= rollingdays:
                if history[i] - history[i-1] > 0:
                    gain.append((history[i] - history[i-1]) / history[i-1])
                else: 
                    loss.append((history[i] - history[i-1]) / history[i-1])
        avg_gain = sum(gain) / rollingdays
        avg_loss = abs(sum(loss) / rollingdays)
        if avg_loss: return avg_gain/avg_loss 
    else:
        return 0

def topRsi (update, hours=24):
    symbols = getSymbols()
    rsilist = {}
    topRsi = "Top Fiat Coins by RSI(24h):"
    
    for symbol in symbols:
        klines = getKlines(hours,symbol)
        rsi_temp = rsi(klines,hours)
        if klines: 
            if rsi_temp:
                RSI_index = 100 - (100 / (1 + rsi_temp))
                rsilist['{}'.format(symbol)] = RSI_index
    
    sorted_symbols = {k: v for k, v in sorted(rsilist.items(), key=lambda item: item[1])}
    y = 0
    for x in list(reversed(list(sorted_symbols)))[0:3]:
        y += 1
        #print (x, sorted_symbols[x])
        topRsi = topRsi + "\n{}) {} - RSI: {: .2f}".format(y,x,sorted_symbols[x])
    updater.bot.send_message(chat_id="@bebelere_balon", text= "{}".format(topRsi))
    
updater.job_queue.run_repeating(topRsi, 3600, first=0)
updater.start_polling()
updater.idle()

