# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '/usr/local/lib/python2.7/site-packages')
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler, CallbackQueryHandler)
import telegram
import logging

from constants import (CREATE_JOURNEY, token, ADD_STOP, MY_JOURNEY, SEARCH)
from connection import (connect_to_database, disconnect_from_database)
import createJourney
import addStop
import myJournies
import Search

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def start(bot, update):
    conn = connect_to_database()
    cur = conn.cursor()
    SQL = "SELECT count(1) FROM users WHERE login = %s;"
    query_data = (update.message.from_user.username,)
    cur.execute(SQL, query_data)
    result = cur.fetchone()[0]
    if result == 0:
        SQL = "INSERT INTO users (user_id, login) VALUES (%s, %s);"
        query_data = (update.message.from_user.id, update.message.from_user.username,)
        cur.execute(SQL, query_data)
        logging.info('user with user_id=%s, username=%s has been added to the database' % (update.message.from_user.id, update.message.from_user.username))

    cur.close()
    disconnect_from_database(conn)
    update.message.reply_text('Hello!\nUse this bot to plan your journeys and participate in journeys of others')


def help(bot, update):
    update.message.reply_text('start - begin interaction\nhelp - list of commands\ncancel - cancel current command\ncreate_journey - basic plan of new journey\nadd_stop - add new stops to the journey consequentially\nmy_journies - see the list of journies you participate in, edit and delete ones you created\nsearch - search for journies to join to')


def cancel(bot, update):
    logger.info("User %s canceled command" % update.message.from_user.username)
    reply_markup = telegram.ReplyKeyboardRemove()
    bot.send_message(chat_id=update.message.chat_id, text="command has been canceled", reply_markup=reply_markup)
    return -1


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

    # cancel_handler = CommandHandler('cancel', cancel)
    # dispatcher.add_handler(cancel_handler)

    create_journey_handler = ConversationHandler(
        entry_points=[CommandHandler('create_journey', createJourney.create_journey)],

        states={
            CREATE_JOURNEY['NAME']: [MessageHandler(Filters.text, createJourney.add_name)],

            CREATE_JOURNEY['DEPARTURE_PLACE']: [MessageHandler(Filters.text, createJourney.add_departure_point)],

            CREATE_JOURNEY['DESTINATION']: [MessageHandler(Filters.text, createJourney.add_destination)],

            CREATE_JOURNEY['DEPARTURE_DATE']: [MessageHandler(Filters.text, createJourney.add_departure_date)],

            CREATE_JOURNEY['ARRIVAL_DATE']: [MessageHandler(Filters.text, createJourney.add_arrival_date)],

            CREATE_JOURNEY['PUBLICITY_AND_ADDING']: [MessageHandler(Filters.text, createJourney.add_publicity)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(create_journey_handler)

    add_stop_handler = ConversationHandler(
        entry_points=[CommandHandler('add_stop', addStop.add_stop)],

        states={
            ADD_STOP['JOURNEY_NAME']: [MessageHandler(Filters.text, addStop.add_journey_name)],

            ADD_STOP['DEPARTURE_PLACE']: [MessageHandler(Filters.text, addStop.add_departure_place)],

            ADD_STOP['DESTINATION']: [MessageHandler(Filters.text, addStop.add_destination)],

            ADD_STOP['DEPARTURE_TIME']: [MessageHandler(Filters.text, addStop.add_departure_time)],

            ADD_STOP['ARRIVAL_TIME']: [MessageHandler(Filters.text, addStop.add_arrival_time)],

            ADD_STOP['PRICE']: [MessageHandler(Filters.text, addStop.add_price)],

            ADD_STOP['TYPE']: [MessageHandler(Filters.text, addStop.add_type)],

            ADD_STOP['IS_SHEDULED']: [MessageHandler(Filters.text, addStop.add_is_scheduled)],

            ADD_STOP['CHOOSEN']: [CallbackQueryHandler(addStop.choosen)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(add_stop_handler)

    my_journies_handler = ConversationHandler(
        entry_points=[CommandHandler('my_journies', myJournies.my_journies)],

        states={
            MY_JOURNEY['SHOW_OR_DELETE_JOURNEY']: [CallbackQueryHandler(myJournies.show_or_delete_journey)],

            MY_JOURNEY['EDITING']: [CallbackQueryHandler(myJournies.edit_journey)]

        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(my_journies_handler)

    search_handler = ConversationHandler(
        entry_points=[CommandHandler('search', Search.search)],

        states={
            SEARCH['DEPARTURE_POINT']: [MessageHandler(Filters.text, Search.add_departure_point)],

            SEARCH['DESTINATION']: [MessageHandler(Filters.text, Search.add_destination)],

            SEARCH['DEPARTURE_DATE']: [MessageHandler(Filters.text, Search.add_departure_date)],

            SEARCH['ARRIVAL_DATE']: [MessageHandler(Filters.text, Search.add_arrival_date)],

            SEARCH['BUDGET']: [MessageHandler(Filters.text, Search.add_budget)],

            SEARCH['PLACES']: [MessageHandler(Filters.text, Search.add_place)],

            SEARCH['SHOW_OR_JOIN_OR_OTHERS']: [CallbackQueryHandler(Search.show_or_join_or_others)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(search_handler)

    #updater.dispatcher.add_handler(CallbackQueryHandler(addStop.choosen))

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
