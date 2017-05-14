from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import logging

from connection import (connect_to_database, disconnect_from_database)
from constants import MY_JOURNEY


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

data = {}

def my_journies(bot, update):
    data['no_stops_left'] = False
    logger.info("Journies %s participates in" % update.message.from_user.username)
    data['chat_id'] = update.message.chat_id
    user_id = update.message.from_user.id
    data['user_id'] = user_id
    conn = connect_to_database()
    cur = conn.cursor()
    SQL = """
      WITH j_id AS (
        SELECT  journey_id, is_host
        FROM    travelers
        WHERE   user_id = %s
      )  
      
      SELECT  journey_id, departure_point, destination, budget, journey_name, departure_date, arrival_date, is_host
      FROM    journey 
      NATURAL JOIN j_id;"""
    query_data = (user_id,)
    cur.execute(SQL, query_data)
    journies = cur.fetchall()
    cur.close()
    disconnect_from_database(conn)
    if len(journies) == 0:
        update.message.reply_text('You have no journies, first use /create_journey command')
        return -1

    for row in journies:
        if row[7]:
            keyboard = [[InlineKeyboardButton("Show", callback_data='s' + str(row[0])),
                        InlineKeyboardButton("Delete", callback_data='d' + str(row[0]))]]
        else:
            keyboard = [[InlineKeyboardButton("Show", callback_data='s' + str(row[0]))]]
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

    keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text='to cancel press', reply_markup=reply_markup)
    data['journey_been_pushed'] = False

    return MY_JOURNEY['SHOW_OR_DELETE_JOURNEY']


def show_or_delete_journey(bot, update):
    if data['journey_been_pushed']:
        return
    data['journey_been_pushed'] = True
    choice = update.callback_query
    if choice.data == 'cancel':
        bot.sendMessage(chat_id=data['chat_id'], text='continue interaction using commands')
        logger.info("my_journies command canceled")
        return -1

    conn = connect_to_database()
    cur = conn.cursor()
    journey_id = int(choice.data[1:])
    data['journey_id'] = journey_id
    if choice.data[0] == 'd': #delete
        SQL = "SELECT journey_name FROM journey WHERE journey_id = %s;"
        query_data = (journey_id,)
        cur.execute(SQL, query_data)
        journey_name = cur.fetchone()[0]
        logger.info("deleting of journey %s", journey_name)

        SQL = "DELETE FROM journey WHERE journey_id = %s"
        query_data = (journey_id,)
        cur.execute(SQL, query_data)
        cur.close()
        disconnect_from_database(conn)
        bot.sendMessage(chat_id=data['chat_id'], text='Journey %s has been deleted' % (journey_name,))
        return

    else:
        SQL = "SELECT is_host FROM travelers WHERE user_id = %s AND journey_id = %s"
        query_data = (data['user_id'], data['journey_id'])
        cur.execute(SQL, query_data)
        data['is_host'] = cur.fetchone()[0]
        data['button_number'] = 0
        show(cur, conn, bot, update)

        return MY_JOURNEY['EDITING']


def edit_journey(bot, update):
    choice = update.callback_query
    delete_start = choice.data.find('delete')
    leave_start = choice.data.find('leave')
    if leave_start != -1:
        number_of_button = int(choice.data[:leave_start])
        if number_of_button != data['button_number']:
            logger.info("leave already pushed")
            return MY_JOURNEY['EDITING']
        else:
            logger.info("journey has been left as it was")
            SQL = "SELECT journey_name FROM journey WHERE journey_id = %s;"
            query_data = (data['journey_id'],)
            conn = connect_to_database()
            cur = conn.cursor()
            cur.execute(SQL, query_data)
            journey_name = cur.fetchone()[0]
            disconnect_from_database(conn)
            bot.sendMessage(chat_id=data['chat_id'], text="Journey %s has been saved" % (journey_name,))
            return -1
    elif delete_start != -1:
        number_of_button = int(choice.data[:delete_start])
        if number_of_button != data['button_number']:
            logger.info("delete already pushed")
            return MY_JOURNEY['EDITING']
    else:
        bot.sendMessage(chat_id=data['chat_id'], text='continue interaction using commands')
        logger.info("my_journies command canceled")
        return -1

    logger.info("journey's last stop will be deleted")
    conn = connect_to_database()
    cur = conn.cursor()
    last_stop_id = int(choice.data[delete_start + 6:])
    SQL = 'SELECT transport_id_for_arrival FROM stops WHERE stop_id = %s;'
    query_data = (last_stop_id,)
    cur.execute(SQL, query_data)
    deleted_transport_id_for_arrival = cur.fetchone()[0]

    SQL = 'UPDATE stops SET transport_id_for_department = %s WHERE journey_id = %s AND transport_id_for_department = %s;'
    query_data = (None, data['journey_id'], deleted_transport_id_for_arrival,)
    cur.execute(SQL, query_data)

    SQL = "SELECT first_stop FROM journey WHERE journey_id = %s"
    query_data = (data['journey_id'],)
    cur.execute(SQL, query_data)
    first_stop_id = cur.fetchone()[0]

    if first_stop_id == last_stop_id:
        SQL = "UPDATE journey SET first_stop = %s WHERE journey_id = %s"
        query_data = (None, data['journey_id'])
        cur.execute(SQL, query_data)
        data['no_stops_left'] = True

    SQL = "DELETE FROM stops WHERE stop_id = %s;"
    query_data = (last_stop_id,)
    cur.execute(SQL, query_data)

    bot.sendMessage(chat_id=data['chat_id'], text='Last stop has been deleted')

    show(cur, conn, bot, update)

    return MY_JOURNEY['EDITING']


def show(cur, conn, bot, update):
    SQL = "SELECT first_stop, journey_name FROM journey WHERE journey_id = %s"
    query_data = (data['journey_id'],)
    cur.execute(SQL, query_data)
    result = cur.fetchone()
    if result[0] is None:
        data['no_stops_left'] = True
        bot.sendMessage(chat_id=data['chat_id'], text='Journey has no stops yet\nUse /add_stop to add stops to the journey')
        return -1

    journey_name = result[1]
    bot.sendMessage(chat_id=data['chat_id'], text=journey_name.upper())

    first_stop_id = result[0]
    print first_stop_id

    SQL = """
            SELECT  stop_id, transport_id_for_arrival, transport_id_for_department
            FROM    stops
            WHERE   journey_id = %s"""
    query_data = (data['journey_id'],)
    cur.execute(SQL, query_data)
    stops = cur.fetchall()
    print stops

    data['last_stop_id'] = first_stop_id
    next_transport_id_for_arrival = -1
    last = False
    for row in stops:
        if row[0] == first_stop_id:
            next_transport_id_for_arrival = row[2]
            if len(stops) == 1:
                last = True
            print_transport(cur, bot, row, last)
            stops.remove(row)
            break

    for i in range(len(stops)):
        for row in stops:
            if row[1] == next_transport_id_for_arrival:
                next_transport_id_for_arrival = row[2]
                if len(stops) == 1:
                    last = True
                print_transport(cur, bot, row, last)
                data['last_stop_id'] = row[0]
                stops.remove(row)
                break

    cur.close()
    disconnect_from_database(conn)


def print_transport(cur, bot, row, last):
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
        data['button_number'] += 1
        if data['is_host']:
            keyboard = [[InlineKeyboardButton('delete last stop', callback_data=str(data['button_number']) + 'delete' + str(data['last_stop_id']))],
                        [InlineKeyboardButton('leave', callback_data=str(data['button_number']) + 'leave')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.sendMessage(chat_id=data['chat_id'], text=message_text, reply_markup=reply_markup)
            data['stop_been_pushed' + str(data['button_number'])] = False
        else:
            bot.sendMessage(chat_id=data['chat_id'], text=message_text)
            return -1
    else:
        bot.sendMessage(chat_id=data['chat_id'], text=message_text)