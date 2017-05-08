# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '/usr/local/lib/python2.7/site-packages')
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler)
import telegram
import logging

from constants import (CREATE_JOURNEY, token)
import createJourney
from connection import (connect_to_database, disconnect_from_database)


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def start(bot, update):
    conn = connect_to_database()
    cur = conn.cursor()
    SQL = "SELECT count(1) FROM users WHERE login = %s;"
    data = (update.message.from_user.username,)
    cur.execute(SQL, data)
    result = cur.fetchone()[0]
    if result == 0:
        SQL = "INSERT INTO users (user_id, login) VALUES (%s, %s);"
        data = (update.message.from_user.id, update.message.from_user.username,)
        cur.execute(SQL, data)
        disconnect_from_database(conn)
        logging.info('user with user_id=%s, username=%s has been added to the database' % (update.message.from_user.id, update.message.from_user.username))

    update.message.reply_text('Hello!\nUse this bot to plan your journeys and participate in journeys of others')


def help(bot, update):
    update.message.reply_text('list of commands')


def cancel(bot, update):
    logger.info("User %s canceled command" % update.message.from_user.username)
    update.message.reply_text('command has been canceled')


def unknown(bot, update):
    update.message.reply_text('unknown command')


def error(bot, update, error):
    logger.info('Update "%s" caused error "%s"' % (update, error))


def main():
    bot = telegram.Bot(token=token)

    updater = Updater(token=token)

    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    dispatcher.add_handler(help_handler)

    cancel_handler = CommandHandler('cancel', cancel)
    dispatcher.add_handler(cancel_handler)

    create_journey_handler = ConversationHandler(
        entry_points=[CommandHandler('create_journey', createJourney.create_journey)],

        states={
            CREATE_JOURNEY['NAME']: [MessageHandler(Filters.text, createJourney.add_name)],

            CREATE_JOURNEY['DEPARTURE_PLACE']: [MessageHandler(Filters.text, createJourney.add_departure_point)],

            CREATE_JOURNEY['DESTINATION']: [MessageHandler(Filters.text, createJourney.add_destination)],

            CREATE_JOURNEY['DEPARTURE_DATE']: [MessageHandler(Filters.text, createJourney.add_departure_date)],

            CREATE_JOURNEY['ARRIVAL_DATE']: [MessageHandler(Filters.text, createJourney.add_arrival_date)],

            CREATE_JOURNEY['BUDGET']: [MessageHandler(Filters.text, createJourney.add_budget)],

            CREATE_JOURNEY['PUBLICITY_AND_ADDING']: [MessageHandler(Filters.text, createJourney.add_publicity)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(create_journey_handler)

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
    
