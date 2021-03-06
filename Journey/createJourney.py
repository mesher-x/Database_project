from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
import logging

from connection import (connect_to_database, disconnect_from_database)
from constants import CREATE_JOURNEY


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


data = {} #to save user input before uploading to database


def create_journey(bot, update):
    logger.info("%s creates a journey" % update.message.from_user.username)
    update.message.reply_text('Input journey name')

    return CREATE_JOURNEY['NAME']


def add_name(bot, update):
    journey_name = update.message.text
    conn = connect_to_database()
    cur = conn.cursor()
    SQL = """
            SELECT 	count(1)
            FROM	journey
        	NATURAL JOIN travelers
            WHERE 	user_id = %s
                    AND journey_name = %s;
            """
    query_data = (update.message.from_user.id, journey_name,)
    cur.execute(SQL, query_data)
    result = cur.fetchone()[0]
    cur.close()
    disconnect_from_database(conn)
    if result != 0:
        update.message.reply_text('You already have journey named %s, choose another name' % journey_name)
        return CREATE_JOURNEY['NAME']
    data['name'] = journey_name
    logger.info("%s named his journey %s" % (update.message.from_user.username, update.message.text))
    update.message.reply_text('Input place of departure')

    return CREATE_JOURNEY['DEPARTURE_PLACE']


def add_departure_point(bot, update):
    data['departure_point'] = update.message.text.lower()
    logger.info("%s's journey starts from %s" % (update.message.from_user.username, update.message.text))
    update.message.reply_text('Input destination')

    return CREATE_JOURNEY['DESTINATION']


def add_destination( bot, update):
    data['destination'] = update.message.text.lower()
    logger.info("%s's journey ends at %s" % (update.message.from_user.username, update.message.text))
    update.message.reply_text('Input departure date(year-month-day, 0 for not stated)')

    return CREATE_JOURNEY['DEPARTURE_DATE']


def add_departure_date( bot, update):
    data['departure_date'] = update.message.text if update.message.text != '0' else None
    logger.info("%s's journey starts at %s" % (update.message.from_user.username, data['departure_date']))
    update.message.reply_text('Input arrival date(year-month-day, 0 for not stated)')

    return CREATE_JOURNEY['ARRIVAL_DATE']


def add_arrival_date( bot, update):
    data['arrival_date'] = update.message.text if update.message.text != '0' else None
    logger.info("%s's journey ends at %s" % (update.message.from_user.username, data['arrival_date']))
    reply_keyboard = [['Yes', 'No']]
    update.message.reply_text('Do you want this journey to appear in search results?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return CREATE_JOURNEY['PUBLICITY_AND_ADDING']


def add_publicity( bot, update):
    data['publicity'] = (update.message.text.lower() == 'yes')
    put_in_database(bot, update)

    return -1


def put_in_database( bot, update):
    try:
        conn = connect_to_database()
        cur = conn.cursor()
        #new journey
        SQL = "INSERT INTO journey (journey_name, departure_point, destination, departure_date, arrival_date, is_public) VALUES (%s, %s, %s, %s, %s, %s);"
        query_data = (data['name'], data['departure_point'], data['destination'], data['departure_date'], data['arrival_date'], data['publicity'],)
        cur.execute(SQL, query_data)
        logger.info("%s's journey %s has been putted in database" % (update.message.from_user.username, data['name']))
        #what journey_id does new journey have
        SQL = "SELECT currval('journey_journey_id_seq');"
        cur.execute(SQL)
        journey_id = cur.fetchone()[0]
        #accordance of user and journey
        SQL = "INSERT INTO travelers (journey_id, user_id, is_host) VALUES (%s, %s, %s);"
        query_data = (journey_id, update.message.from_user.id, True)
        cur.execute(SQL, query_data)
        cur.close()
        disconnect_from_database(conn)
        logger.info("%s participates in journey %s" % (update.message.from_user.username, data['name']))
        update.message.reply_text('Congratulations, journey ' + data['name'] + ' has been created')
    except Exception as e:
        update.message.reply_text('wrong input, journey ' + data['name'] + ' has not been created')
        logger.info("Exception %s has happened" % e)