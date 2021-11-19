from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
import os
import predict

telegram_token = '*'
updater = Updater(telegram_token, use_context=True)

def makePrediction(update):

    updater.bot.send_message(chat_id="@guuru_crypto", text="Prediction engine started.")
    p = predict.predict()
    updater.bot.send_message(chat_id="@guuru_crypto", text="Tomorrow's BTC prediction is ${}.".format(str(p)))

def main():

    dp = updater.dispatcher
    #dp.add_handler(CommandHandler("predict", makePrediction))
    updater.job_queue.run_repeating(makePrediction, 86400, first=10)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()