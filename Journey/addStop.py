from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
import logging

from connection import (connect_to_database, disconnect_from_database)
from constants import ADD_STOP


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


data = {} #to save user input before uploading to database

def is_first(bot, update, cur):
    SQL = "SELECT currval('stops_stop_id_seq');"
    cur.execute(SQL)
    stop_id = cur.fetchone()[0]

    SQL = "UPDATE journey SET first_stop = %s WHERE journey_id = %s;"
    query_data = (stop_id, data['journey_id'])
    cur.execute(SQL, query_data)


def add_stop(bot, update):
    logger.info("%s chooses the journey to add stop to" % update.message.from_user.username)
    conn = connect_to_database()
    cur = conn.cursor()
    SQL = """
    SELECT 	journey_name 
    FROM	journey
	NATURAL JOIN travelers t
    WHERE 	t.user_id = %s;
    """
    query_data = (update.message.from_user.id,)
    cur.execute(SQL, query_data)
    journey_names = cur.fetchall()
    cur.close()
    disconnect_from_database(conn)
    if len(journey_names) == 0:
        update.message.reply_text('You have no journies to add stop to, first use /create_journey command')
        return -1 #end of conversation

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
                AND journey_name = %s;
        """
    query_data = (update.message.from_user.id, journey_name)
    cur.execute(SQL, query_data)
    result = cur.fetchone()
    cur.close()
    disconnect_from_database(conn)
    data['journey_id'] = result[0]
    data['is_first'] = (result[1] == None)
    update.message.reply_text('input place of departure')

    return ADD_STOP['DEPARTURE_PLACE']


def add_departure_place(bot, update):
    data['departure_place'] = update.message.text.lower()
    update.message.reply_text('input destination')

    return ADD_STOP['DESTINATION']


def add_destination(bot, update):
    data['destination'] = update.message.text.lower()
    update.message.reply_text('input departure date(and time), format: 2000-01-01 (00:01)')

    return ADD_STOP['DEPARTURE_TIME']


def add_departure_time(bot, update):
    data['departure_time'] = update.message.text + ':00'
    update.message.reply_text('input arival date(and time), format: 2000-01-01 (00:01)')

    return ADD_STOP['ARRIVAL_TIME']


def add_arrival_time(bot, update):
    data['arrival_time'] = update.message.text + ':00'
    update.message.reply_text('input price(0 for not stated)')

    return ADD_STOP['PRICE']


def add_price(bot, update):
    data['price'] = update.message.text if update.message.text != '0' else None
    update.message.reply_text('input type of the transport(0 for not stated)')

    return ADD_STOP['TYPE']


def add_type(bot, update):
    data['type'] = update.message.text.lower() if update.message.text != '0' else None
    reply_keyboard = [['Yes', 'No']]
    update.message.reply_text('do you want to see suitable for you scheduled transport?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return ADD_STOP['IS_SHEDULED']


def add_is_scheduled(bot, update):
    show_suitable_transport = (update.message.text == 'Yes')
    conn = connect_to_database()
    cur = conn.cursor()
    if not show_suitable_transport:
        SQL = "INSERT INTO transport (departure_point, destination, departure_time, arrival_time, price, type, is_scheduled) VALUES (%s, %s, %s, %s, %s, %s, %s);"
        query_data = (data['departure_place'], data['destination'], data['departure_time'], data['arrival_time'], data['price'], data['type'], False,)
        cur.execute(SQL, query_data)

        SQL = "SELECT currval('transport_transport_id_seq');"
        cur.execute(SQL)
        transport_id = cur.fetchone()[0]

        SQL = "INSERT INTO stops (journey_id, transport_id_for_arrival) VALUES (%s, %s);"
        query_data = (data['journey_id'], transport_id)
        cur.execute(SQL, query_data)
    else:
        #show available transport with buttons to choose
        return ADD_STOP['transport from database']

    if data['is_first']:
        is_first(bot, update, cur)




    cur.close()
    disconnect_from_database(conn)
    return -1

def add_stop(bot, update):
    choice = update.message.text()
    if choice != 'cancel':
        #insert stop in database with scheduled transport
    else:
        #do  if not suitable transport from add_is_schedueld


    if data['is_first']:
        is_first(bot, update, cur)

    cur.close()
    disconnect_from_database(conn)

    return -1
