# -*- coding: utf-8 -*-
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import logging

from connection import (connect_to_database, disconnect_from_database)
from constants import SEARCH


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

data = {}

Search = {
    'DEPARTURE_POINT': 0,
    'DESTINATION': 1,
    'DEPARTURE_DATE': 2,
    'ARRIVAL_DATE': 3,
    'BUDGET': 4,
    'PLACES': 5
}

def search(bot, update):
    data['chat_id'] = update.message.chat_id
    data['user_id'] = update.message.from_user.id
    logger.info("%s searches for journies" % update.message.from_user.username)
    update.message.reply_text('Input departure point(0 for not stated)')

    return SEARCH['DEPARTURE_POINT']


def add_departure_point(bot, update):
    data['departure_point'] = update.message.text.lower() if update.message.text != '0' else None
    logger.info("%s searches for that starts from %s" % (update.message.from_user.username, update.message.text))
    update.message.reply_text('Input destination(0 for not stated)')

    return SEARCH['DESTINATION']


def add_destination(bot, update):
    data['destination'] = update.message.text.lower() if update.message.text != '0' else None
    logger.info("%s searches for that starts from %s" % (update.message.from_user.username, update.message.text))
    update.message.reply_text('Input departure date(year-month-day, 0 for not stated)')

    return SEARCH['DEPARTURE_DATE']


def add_departure_date(bot, update):
    data['departure_date'] = update.message.text if update.message.text != '0' else None
    logger.info("%s searches for journey that starts at %s" % (update.message.from_user.username, data['departure_date']))
    update.message.reply_text('Input arrival date(year-month-day, 0 for not stated)')

    return SEARCH['ARRIVAL_DATE']


def add_arrival_date(bot, update):
    data['arrival_date'] = update.message.text if update.message.text != '0' else None
    logger.info("%s searches for journey that ends at %s" % (update.message.from_user.username, data['arrival_date']))
    update.message.reply_text('Input maximum budget(0 for unlimited)')

    return SEARCH['BUDGET']


def add_budget(bot, update):
    data['budget'] = update.message.text if update.message.text != '0' else None
    logger.info("%s searches for journey that costs no more than %s" % (update.message.from_user.username, data['arrival_date']))
    update.message.reply_text('Input all places you would like to visit \nformat: town1, town2,... (0 for not stated)')

    return SEARCH['PLACES']


def add_place(bot, update):
    if update.message.text != '0':
        towns_list = update.message.text.split(', ')
        towns = ''
        for town in towns_list:
            towns += "'" + town + "'" + ', '

        towns = towns[:-2]
    else:
        towns = update.message.text

    SQL = ''
    wholeSQL = ''
    query_data = []
    need_and = False
    need_where = False
    for key, value in data.iteritems():
        if key != 'towns' and key != 'user_id' and key != 'chat_id' and value is not None:
            need_where = True
    if need_where:
        SQL += 'SELECT journey_id FROM journey WHERE '
        if data['departure_point'] is not None:
            SQL += 'departure_point = %s '
            query_data.append(data['departure_point'])
            need_and = True

        if data['destination'] is not None:
            if need_and:
                SQL += 'AND '
            SQL += 'destination = %s '
            query_data.append(data['destination'])
            need_and = True

        if data['departure_date'] is not None:
            if need_and:
                SQL += 'AND '
            SQL += 'departure_date >= %s '
            query_data.append(data['departure_date'])
            need_and = True

        if data['arrival_date'] is not None:
            if need_and:
                SQL += 'AND '
            SQL += 'arrival_date <= %s '
            query_data.append(data['arrival_date'])
            need_and = True

        if data['budget'] is not None:
            if need_and:
                SQL += 'AND '
            SQL += 'budget <= %s '
            query_data.append(data['budget'])

        SQL += 'AND is_public = True'
    else:
        SQL = 'SELECT journey_id FROM journey WHERE is_public = True'

    wholeSQL += 'WITH journey_ids AS (' + SQL + ')'
    if towns != '0':
        wholeSQL += ", journey_transport AS ( SELECT journey_id, transport_id_for_arrival FROM stops NATURAL JOIN journey_ids) " + \
                    "SELECT journey_id FROM journey_transport NATURAL JOIN transport WHERE destination in (" + towns + ") "
    else:
        wholeSQL += 'SELECT journey_id FROM journey_ids '

    data['wholeSQl'] = wholeSQL
    data['query_data'] = query_data
    data['offset'] = 0

    show_journies(update)

    return SEARCH['SHOW_OR_JOIN_OR_OTHERS']


def show_journies(update):
    if data['offset'] == 0:
        wholeSQL = data['wholeSQl'] + 'LIMIT 11;'
    else:
        wholeSQL = data['wholeSQl'] + 'OFFSET ' + data['offset'] + 'LIMIT 11;'
    conn = connect_to_database()
    cur = conn.cursor()
    if len(data['query_data']) != 0:
        cur.execute(wholeSQL, tuple(data['query_data']))
    else:
        cur.execute(wholeSQL)
    journey_ids = cur.fetchall()
    data['rows_amount'] = len(journey_ids)

    if data['rows_amount'] == 0:
        update.message.reply_text('There are no journies that would suit you')
        return -1

    journey_ids_list = []
    for i in range(min(data['rows_amount'], 10)):
        journey_ids_list.append(journey_ids[i][0])

    SQL = """
          SELECT  journey_id, departure_point, destination, budget, journey_name, departure_date, arrival_date
          FROM    journey 
          WHERE journey_id in """ + str(tuple(journey_ids_list))[:-2] + ')' + ';'
    cur.execute(SQL)
    journies = cur.fetchall()
    cur.close()
    disconnect_from_database(conn)

    for row in journies:
        keyboard = [[InlineKeyboardButton("Show", callback_data='s' + str(row[0])),
                        InlineKeyboardButton("Join", callback_data='j' + str(row[0]))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = row[4].upper() + '\ndeparture:\n place: ' + row[1]
        if row[5] is not None:
            message_text += '    date: ' + str(row[5])[:10]
        message_text += '\narrival:\n place: ' + row[2]
        if row[6] is not None:
            message_text += '    date: ' + str(row[6])[:10]
        if row[3] is not None:
            message_text += '\nbudget: ' + row[3]
        update.message.reply_text(text=message_text, reply_markup=reply_markup)

    if data['rows_amount'] > 10:
        keyboard = [[InlineKeyboardButton("others", callback_data='see')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text='to see other journies press', reply_markup=reply_markup)

    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text='to cancel press', reply_markup=reply_markup)
    data['cancel_been_pushed'] = False


def show_or_join_or_others(bot, update):
    if data['cancel_been_pushed']:
        return -1
    choice = update.callback_query
    if choice.data == 'cancel':
        data['cancel_been_pushed'] = True
        bot.sendMessage(chat_id=data['chat_id'], text='command /search has been canceled\ncontinue interaction using commands')
        logger.info("search command canceled")
        return -1

    if choice.data == 'see':
        data['offset'] += 10
        show_journies(update)
    elif choice.data.find('j') != -1:
        journey_id = int(choice.data[1:])
        join(journey_id, update, bot)
    else: # show journey
        journey_id = int(choice.data[1:])
        show(bot, journey_id)
        #
        # keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
        # reply_markup = InlineKeyboardMarkup(keyboard)
        # bot.sendMessage(chat_id=data['chat_id'], text='to cancel press', reply_markup=reply_markup)

    return SEARCH['SHOW_OR_JOIN_OR_OTHERS']


def join(journey_id, update, bot):
    user_id = data['user_id']
    conn = connect_to_database()
    cur = conn.cursor()

    SQL = 'SELECT journey_name FROM journey WHERE journey_id = %s'
    query_data = (journey_id,)
    cur.execute(SQL, query_data)
    journey_name = cur.fetchone()[0]

    SQL = 'SELECT is_host FROM travelers WHERE user_id = %s AND journey_id = %s;'
    query_data = (user_id, journey_id,)
    cur.execute(SQL, query_data)
    result = cur.fetchone()

    if result is None:
        SQL = 'INSERT INTO travelers (user_id, journey_id, is_host) VALUES (%s, %s, False);'
        query_data = (user_id, journey_id,)
        cur.execute(SQL, query_data)
        bot.sendMessage(chat_id=data['chat_id'], text='You have joined journey %s' % (journey_name,))
    else:
        is_host = result[0]
        if is_host:
            bot.sendMessage(chat_id=data['chat_id'], text='Silly, journey %s is yours)'% (journey_name,))
        else:
            bot.sendMessage(chat_id=data['chat_id'], text='You already participate in journey %s' % (journey_name,))

    cur.close()
    disconnect_from_database(conn)


def show(bot, journey_id):
    conn = connect_to_database()
    cur = conn.cursor()
    SQL = "SELECT first_stop, journey_name FROM journey WHERE journey_id = %s"
    query_data = (journey_id,)
    cur.execute(SQL, query_data)
    row = cur.fetchone()
    journey_name = row[1]
    first_stop_id = row[0]
    if first_stop_id is None:
        bot.sendMessage(chat_id=data['chat_id'], text='Journey %s has no stops' % (journey_name,))
        return

    bot.sendMessage(chat_id=data['chat_id'], text=journey_name.upper())

    SQL = """
            SELECT  stop_id, transport_id_for_arrival, transport_id_for_department
            FROM    stops
            WHERE   journey_id = %s"""
    query_data = (journey_id,)
    cur.execute(SQL, query_data)
    stops = cur.fetchall()

    next_transport_id_for_arrival = -1
    last = False
    for row in stops:
        if row[0] == first_stop_id:
            next_transport_id_for_arrival = row[2]
            if len(stops) == 1:
                last = True
            print_transport(cur, bot, row, last, journey_id)
            stops.remove(row)
            break

    for i in range(len(stops)):
        for row in stops:
            if row[1] == next_transport_id_for_arrival:
                next_transport_id_for_arrival = row[2]
                if len(stops) == 1:
                    last = True
                print_transport(cur, bot, row, last, journey_id)
                stops.remove(row)
                break

    cur.close()
    disconnect_from_database(conn)



def print_transport(cur, bot, row, last, journey_id):
    SQL = """
        SELECT  departure_point, destination, departure_time, arrival_time, price, type, is_scheduled
        FROM    transport
        WHERE   transport_id = %s"""
    query_data = (row[1],)
    cur.execute(SQL, query_data)
    transport = cur.fetchone()
    message_text = 'departure:\n place: ' + transport[0] + '    time: ' + str(transport[2])[:16] + '\narrival:\n place: ' + transport[1] + '    time: ' + str(transport[3])[:16]
    if transport[4] is not None:
        message_text += '\nprice: ' + transport[4]
    if transport[5] != 'any':
        message_text += '\ntype: ' + transport[5]
    message_text += '\nscheduled' if transport[6] else '\nnot scheduled'

    if last:
        keyboard = [[InlineKeyboardButton("Join", callback_data='j' + str(journey_id))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.sendMessage(chat_id=data['chat_id'], text=message_text, reply_markup=reply_markup)
    else:
        bot.sendMessage(chat_id=data['chat_id'], text=message_text)
