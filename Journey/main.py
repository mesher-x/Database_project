# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, '/usr/local/lib/python2.7/site-packages')
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler)
import logging
import psycopg2

import constants
import createJourney








def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text='Hello!\nUse this bot to plan your journeys and participate in journeys of others')


def help(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text='list of commands')


def cancel(bot, update):
    logger.info("User %s canceled command" % update.message.from_user.username)
    update.message.reply_text('command has been canceled')


def unknown(bot, update):
    update.message.reply_text('unknown command')


def master(bot, update):
    state = check_state(bot, update)
    if update.message.text == '/cancel':
        cancel(bot, update)
    elif state == 'start':
        #commands
        if update.message.text == '/start':
            start(bot, update)
        elif update.message.text == '/help':
            help(bot, update)
        elif update.message.text == '/cancel':
            cancel(bot, update)
        elif update.message.text == '/create_journey':
            createJourney.create_journey(bot, update)
        elif update.message.text == '/add_stop':
            addStop.add_stop(bot, update)
        else:
            unknown(bot, update)
    #inside commands
    elif state.find('/create_journey') != -1:
        createJourney.journey_info.choose_action(state, bot, update)
    elif state.find('/add_stop') != -1:
        addStop.stop_info.choose_action(state, bot, update)


def check_state(bot, update):
    cur = connection.conn.cursor()
    user_id = update.message.from_user.id
    SQL = "SELECT user_id, login, state FROM users WHERE user_id = %s;"
    data = (user_id,)
    cur.execute(SQL, data)
    result = cur.fetchone()
    if result is None:
        SQL = "INSERT INTO users (user_id, login, state) VALUES (%s, %s, %s);"
        login = update.message.from_user.username
        data = (user_id, login, 'start')
        cur.execute(SQL, data)
        bot.sendMessage(chat_id=update.message.chat_id, text='Greetings message')
        return 'start'
    else:
        return result[2]


def error(bot, update, error):
    logger.info('Update "%s" caused error "%s"' % (update, error))


def main():
    bot = telegram.Bot(token=constants.token)

    updater = Updater(token=constants.token)

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    dispatcher = updater.dispatcher

    create_journey_handler = ConversationHandler(
        entry_points=[CommandHandler('create_journey', createJourney.create_journey)],

        states={
            CREATE_JOURNEY_NAME: [MessageHandler(Filters.text, createJourney.journey_info.add_name)],

            CREATE_JOURNEY_DEPARTURE_PLACE: [MessageHandler(Filters.text, createJourney.journey_info.add_departure_point)],

            CREATE_JOURNEY_DESTINATION: [MessageHandler(Filters.text, createJourney.journey_info.add_destination)],

            CREATE_JOURNEY_DEPARTURE_DATE: [MessageHandler(Filters.text, createJourney.journey_info.add_departure_date)],

            CREATE_JOURNEY_ARRIVAL_DATE: [MessageHandler(Filters.text, createJourney.journey_info.add_arrival_date)],

            CREATE_JOURNEY_BUDGET: [MessageHandler(Filters.text, createJourney.journey_info.add_budget)],

            CREATE_JOURNEY_PUBLICITY_AND_ADDING: [MessageHandler(Filters.text, createJourney.journey_info.add_budget)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(create_journey_handler)

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    # master_handler = MessageHandler(Filters.all, master)
    # dispatcher.add_handler(master_handler)

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

#commands: create jorney(name), edit journey, show(гдеб куда чего зачем сколько), connect to journey
# editing of profile - /edit_profile, последовательное заполнение полей, при запросе на внесение информации
# указывать обязательность
# creation of journey - /create, последовательное заполнение полей, при запросе на внесение информации
# указывать обязательность
# editing of journey - новая точка, выбор транспорта
#
