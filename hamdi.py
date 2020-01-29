import telegram.ext
from telegram.ext import Updater, CommandHandler
from telegram.ext import MessageHandler, Filters
import pandas as pd
import json
import numpy as np
from binance.client import Client
import os

# binance setup
binance_api_key = os.environ.get("BINANCE_KEY")
binance_api_secret = os.environ.get("BINANCE_SECRET")
client = Client(binance_api_key, binance_api_secret)

# telegram setup
telegram_token = os.environ.get("TELEGRAM_TOKEN")
updater = Updater(telegram_token, use_context=True)
bot = updater.bot
job = updater.job_queue

#klines = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_1WEEK, "1 Dec, 2017", "1 Jan, 2018")
#print(klines)

def btc_recorder (update, context):
    btc = client.get_symbol_ticker(symbol="BTCUSDT")
    
prices = []
    
for kline in client.get_historical_klines_generator("BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 day ago UTC"):
    prices.append(kline[4])
    
print(prices)

#b = pd.DataFrame(client.get_ticker())
#sozluk = {}
#
#def hello(update, context):
#    update.message.reply_text(
#        'Hello {}'.format(update.message.from_user.first_name))
#    
#def rpta (update):
#    a = pd.DataFrame(client.get_ticker())
#    global b
#    a.volume = a.volume.astype(float)
#    b.volume = b.volume.astype(float)
#    a.lastPrice = a.lastPrice.astype(float)
#    b.lastPrice = b.lastPrice.astype(float)
#    x = b.copy()
#    b = a.copy()
#    for i in range (0, len(a)):
#        c = (a.lastPrice.astype(float).iloc[i] / x.lastPrice.astype(float).iloc[i])
#        d = (a.lastPrice.astype(float).iloc[i] / x.lastPrice.astype(float).iloc[i])
#        #c = format(c, '.5f')
#        c = float("{0:.5f}".format(c))
#        global sozluk
#        z = a.symbol.iloc[i]
#        if c > 1.1:
#            if d > 1.1:
#                sozluk[z] = c
#                
#    result = json.dumps(sozluk)
#    print(bool(sozluk))
#    if bool(sozluk):
#        updater.bot.send_message(chat_id="@bebelere_balon", text= "Hacmi ve fiyati 10% artanlar: \n" + result)
#    sozluk.clear()
#
#updater.job_queue.run_repeating(rpta, 60, first=60)
#updater.dispatcher.add_handler(CommandHandler('hello', hello))

#updater.start_polling()
#updater.idle()