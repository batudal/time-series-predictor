#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
import json
import pandas as pd
import random
import string
import os
import predict

telegram_token = os.getenv("TELEGRAM_TOKEN")
updater = Updater(telegram_token, use_context=True)



dp = updater.dispatcher
dp.add_handler(CommandHandler("g", getPassword))
dp.add_handler(CommandHandler("s", setPassword))
updater.start_polling()
updater.idle()