import logging
import os
import random
import sys
import db
from enum import Enum
import json

from telegram.ext import Updater, Filters, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

# Getting mode, so we could define run function for local and Heroku setup
mode = os.getenv("MODE")
TOKEN = os.getenv("TOKEN")
if mode == "dev":
    def run(updater):
        updater.start_polling()
elif mode == "prod":
    def run(updater):
        PORT = int(os.environ.get("PORT", "8443"))
        HEROKU_APP_NAME = os.environ.get("HEROKU_APP_NAME")
        # Code from https://github.com/python-telegram-bot/python-telegram-bot/wiki/Webhooks#heroku
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TOKEN))
else:
    logger.error("No MODE specified!")
    sys.exit(1)


mydb = db.DB()
  
# creating enumerations using class 
class Fields(Enum): 
    name = 'שם'
    location = 'ישוב'
    phone = 'טלפון'
    address = 'כתובת'
    media = 'מדיה'
    details = 'פרטים'

REPLY=range(1)

def construct_report(reportId):
    report = mydb.getReport(reportId)
    logger.info(report)
    text = 'דיווח מספר {}:\nnext line'.format(reportId)
    keyboard = [[InlineKeyboardButton(Fields.name.value, callback_data=json.dumps({'id':reportId,'option':Fields.name.name})),
                 InlineKeyboardButton(Fields.location.value, callback_data=json.dumps({'id':reportId,'option':Fields.location.name}))],

                [InlineKeyboardButton(Fields.phone.value, callback_data=json.dumps({'id':reportId,'option':Fields.phone.name})),
                 InlineKeyboardButton(Fields.address.value, callback_data=json.dumps({'id':reportId,'option':Fields.address.name}))],

                [InlineKeyboardButton(Fields.media.value, callback_data=json.dumps({'id':reportId,'option':Fields.media.name})),
                 InlineKeyboardButton(Fields.details.value, callback_data=json.dumps({'id':reportId,'option':Fields.details.name}))]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    return [text, reply_markup]

def report_handler(update, context):
    # Creating a handler-function for /start command 
    logger.info("User {} started a new hive report".format(update.effective_user["id"]))
    reportId = mydb.newReport(update.effective_user["id"])

    [text, reply_markup] = construct_report(reportId)

    context.bot.send_message(update.message.chat_id,text, reply_markup=reply_markup)


def button_handler(update, context):
    query = update.callback_query
    data = json.loads(query.data)
    [text, reply_markup] = construct_report(data['id'])
    context.bot.send_message(update.callback_query.message.chat_id,"please enter info")
    return REPLY

def reply_handler(update, context):
    logger.info("user replied")
#    query.edit_message_text(text=text, reply_markup = reply_markup)
    return ConversationHandler.END

def cancel_handler(update, context):
    logger.info("user cancled")
    return ConversationHandler.END


if __name__ == '__main__':
    logger.info("Starting bot")
    updater = Updater(TOKEN, use_context=True)

    updater.dispatcher.add_handler(CommandHandler("report", report_handler))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],

        states={
            REPLY: [MessageHandler(Filters.all, reply_handler)]
        },

        fallbacks=[CommandHandler('cancel', cancel_handler)]
    )

    updater.dispatcher.add_handler(conv_handler)

    run(updater)
