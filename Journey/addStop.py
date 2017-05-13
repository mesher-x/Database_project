from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import logging

from connection import (connect_to_database, disconnect_from_database)
from constants import ADD_STOP


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


data = {} #to save user input before uploading to database


def add_stop(bot, update):
    logger.info("%s adds stop" % update.message.from_user.username)
    data['chat_id'] = update.message.chat_id
    conn = connect_to_database()
    cur = conn.cursor()
    SQL = """
      WITH j_id AS (
        SELECT  journey_id
        FROM    travelers
        WHERE   user_id = %s
      )  

      SELECT  journey_name
      FROM    journey 
      NATURAL JOIN j_id;"""
    query_data = (update.message.from_user.id,)
    cur.execute(SQL, query_data)
    journey_names = cur.fetchall()
    cur.close()
    disconnect_from_database(conn)
    if len(journey_names) == 0:
        update.message.reply_text('You have no journies to add stop to, first use /create_journey command')
        return -1

    reply_keyboard = [[]]
    for journey in journey_names:
        reply_keyboard[0].append(journey[0])
    update.message.reply_text('What journey do you want to add stop to?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return ADD_STOP['JOURNEY_NAME']


def add_journey_name(bot, update):
    journey_name = update.message.text
    conn = connect_to_database()
    cur = conn.cursor()
    SQL = """
        SELECT 	journey_id, first_stop
        FROM	journey
    	NATURAL JOIN travelers
        WHERE 	user_id = %s
                AND journey_name = %s;"""
    query_data = (update.message.from_user.id, journey_name)
    cur.execute(SQL, query_data)
    result = cur.fetchone()
    cur.close()
    disconnect_from_database(conn)
    data['journey_id'] = result[0]
    data['is_first'] = (result[1] is None)
    update.message.reply_text('input place of departure')
    logger.info("%s chooses the journey to add stop to" % update.message.from_user.username)

    return ADD_STOP['DEPARTURE_PLACE']


def add_departure_place(bot, update):
    logger.info("%s inputs place of departure" % update.message.from_user.username)
    data['departure_place'] = update.message.text.lower()
    update.message.reply_text('input destination')

    return ADD_STOP['DESTINATION']


def add_destination(bot, update):
    logger.info("%s inputs destination" % update.message.from_user.username)
    data['destination'] = update.message.text.lower()
    update.message.reply_text('input departure date(and time), format: 2000-01-01 (00:01)')

    return ADD_STOP['DEPARTURE_TIME']


def add_departure_time(bot, update):
    logger.info("%s inputs departure time" % update.message.from_user.username)
    if update.message.text.find(':') == -1:
        data['departure_time'] = update.message.text + ' 00:00:00'
    else:
        data['departure_time'] = update.message.text + ':00'
    update.message.reply_text('input arival date(and time), format: 2000-01-01 (00:01)')

    return ADD_STOP['ARRIVAL_TIME']


def add_arrival_time(bot, update):
    logger.info("%s inputs arrival time" % update.message.from_user.username)
    if update.message.text.find(':') == -1:
        data['arrival_time'] = update.message.text + ' 23:59:00'
    else:
        data['arrival_time'] = update.message.text + ':00'
    update.message.reply_text('input price(0 for not stated)')

    return ADD_STOP['PRICE']


def add_price(bot, update):
    logger.info("%s inputs price" % update.message.from_user.username)
    data['price'] = update.message.text if update.message.text != '0' else None
    update.message.reply_text('input type of the transport(0 for not stated)')

    return ADD_STOP['TYPE']


def add_type(bot, update):
    logger.info("%s inputs type" % update.message.from_user.username)
    data['type'] = update.message.text.lower() if update.message.text != '0' else None
    reply_keyboard = [['Yes', 'No']]
    update.message.reply_text('do you want to see suitable for you scheduled transport?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return ADD_STOP['IS_SHEDULED']


def add_is_scheduled(bot, update):
    logger.info("%s input yes or no" % update.message.from_user.username)
    show_suitable_transport = (update.message.text.lower() == 'yes')
    conn = connect_to_database()
    cur = conn.cursor()
    if show_suitable_transport:
        transport = []
        if data['price'] is None:
            if data['type'] is None:
                SQL = """
                SELECT transport_id, departure_point, destination, departure_time, arrival_time, price, type 
                FROM transport WHERE departure_point = %s AND destination = %s AND departure_time >= %s AND arrival_time <= %s AND is_scheduled = %s;"""
                query_data = (data['departure_place'], data['destination'], data['departure_time'], data['arrival_time'], True,)
                cur.execute(SQL, query_data)
                transport = cur.fetchall()
            else:
                SQL = """
                SELECT transport_id, departure_point, destination, departure_time, arrival_time, price, type  
                FROM transport WHERE departure_point = %s AND destination = %s AND departure_time >= %s AND arrival_time <= %s AND type = %s AND is_scheduled = %s;"""
                query_data = (data['departure_place'], data['destination'], data['departure_time'], data['arrival_time'], data['type'], True,)
                cur.execute(SQL, query_data)
                transport = cur.fetchall()
        else:
            if data['type'] is None:
                SQL = """
                SELECT transport_id, departure_point, destination, departure_time, arrival_time, price, type
                FROM transport WHERE departure_point = %s AND destination = %s AND departure_time >= %s AND arrival_time <= %s AND price <= %s AND is_scheduled = %s;"""
                query_data = (data['departure_place'], data['destination'], data['departure_time'], data['arrival_time'], data['price'], True,)
                cur.execute(SQL, query_data)
                transport = cur.fetchall()
            else:
                SQL = """
                SELECT transport_id, departure_point, destination, departure_time, arrival_time, price, type
                FROM transport WHERE departure_point = %s AND destination = %s AND departure_time >= %s AND arrival_time <= %s AND price <= %s AND type = %s AND is_scheduled = %s;"""
                query_data = (data['departure_place'], data['destination'], data['departure_time'], data['arrival_time'], data['price'], data['type'], True,)
                cur.execute(SQL, query_data)
                transport = cur.fetchall()
        logger.info("transport suitable for %s recieved" % update.message.from_user.username)

        if len(transport) == 0:
            not_scheduled(cur)
            update.message.reply_text('There is no suitable for you transport.\nStop has been added')
            cur.close()
            disconnect_from_database(conn)
            return -1

        cur.close()
        disconnect_from_database(conn)

        for row in transport:
            keyboard = [[InlineKeyboardButton("Select", callback_data=str(row[0]))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(
                'departure:\n place: ' + row[1] + '    time: ' + str(row[3])[:16] + '\narrival:\n place: ' + row[2] + '    time: ' + str(row[4])[:16] + '\nprice: ' + row[5] + '\ntype: ' + row[6],
                reply_markup=reply_markup
            )

        keyboard = [[InlineKeyboardButton("Cancel", callback_data='cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text='to add not scheduled transport press', reply_markup=reply_markup)
        data['been_pushed'] = False

        return ADD_STOP['CHOOSEN']

    else:
        not_scheduled(cur)
        cur.close()
        disconnect_from_database(conn)
        update.message.reply_text('Stop has been added')
        return -1


def not_scheduled(cur):
    if data['type'] is None:
        data['type'] = 'any'
    SQL = "INSERT INTO transport (departure_point, destination, departure_time, arrival_time, price, type, is_scheduled) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    query_data = (data['departure_place'], data['destination'], data['departure_time'], data['arrival_time'], data['price'], data['type'], False,)
    cur.execute(SQL, query_data)

    SQL = "SELECT currval('transport_transport_id_seq');"
    cur.execute(SQL)
    transport_id = cur.fetchone()[0]

    upload_new_stop_and_update_last(cur, transport_id)


def choosen(bot, update):
    if data['been_pushed']:
        return -1
    data['been_pushed'] = True
    choice = update.callback_query
    conn = connect_to_database()
    cur = conn.cursor()
    if choice.data == 'cancel':
        not_scheduled(cur)
    else:
        upload_new_stop_and_update_last(cur, int(choice.data))

    cur.close()
    disconnect_from_database(conn)
    logger.info("stop with scheduled transport has been added")
    bot.sendMessage(chat_id=data['chat_id'], text="Stop has been added")

    return -1


def is_first(cur):
    logger.info("it is first stop")
    SQL = "SELECT currval('stops_stop_id_seq');"
    cur.execute(SQL)
    stop_id = cur.fetchone()[0]

    SQL = "UPDATE journey SET first_stop = %s WHERE journey_id = %s;"
    query_data = (stop_id, data['journey_id'])
    cur.execute(SQL, query_data)


def upload_new_stop_and_update_last(cur, transport_id):
    SQL = "SELECT stop_id FROM stops WHERE journey_id = %s AND transport_id_for_department is %s"
    query_data = (data['journey_id'], None)
    cur.execute(SQL, query_data)
    result = cur.fetchone()
    if result is not None:
        last_stop_id = result[0]
        SQL = "UPDATE stops SET transport_id_for_department = %s WHERE stop_id = %s;"
        query_data = (transport_id, last_stop_id,)
        cur.execute(SQL, query_data)

    SQL = "INSERT INTO stops (journey_id, transport_id_for_arrival) VALUES (%s, %s);"
    query_data = (data['journey_id'], transport_id)
    cur.execute(SQL, query_data)

    if data['is_first']:
        is_first(cur)