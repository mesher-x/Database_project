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
    data['name'] = update.message.text
    logger.info("%s named his journey %s" % (update.message.from_user.username, update.message.text))
    update.message.reply_text('Input place of departure')

    return CREATE_JOURNEY['DEPARTURE_PLACE']

def add_departure_point(bot, update):
    data['departure_point'] = update.message.text
    logger.info("%s's journey starts from %s" % (update.message.from_user.username, update.message.text))
    update.message.reply_text('Input destination')

    return CREATE_JOURNEY['DESTINATION']

def add_destination( bot, update):
    data['destination'] = update.message.text
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
    update.message.reply_text('Input estimated budget(0 for not stated)')

    return CREATE_JOURNEY['BUDGET']

def add_budget( bot, update):
    data['budget'] = update.message.text if update.message.text != '0' else None
    logger.info("%s's journey estimated cost is %s" % (update.message.from_user.username, data['budget']))
    reply_keyboard = [['Yes', 'No']]
    update.message.reply_text('Do you want this journey to appear in search results?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return CREATE_JOURNEY['PUBLICITY_AND_ADDING']

def add_publicity( bot, update):
    data['publicity'] = (update.message.text.lower() == 'Yes')
    put_in_database(bot, update)

    return -1 #end of conversation

def put_in_database( bot, update):
    try:
        conn = connect_to_database()
        cur = conn.cursor()
        #new journey
        SQL = "INSERT INTO journey (journey_name, departure_point, destination, departure_date, arrival_date, is_public, budget) VALUES (%s, %s, %s, %s, %s, %s, %s);"
        _data = (data['name'], data['departure_point'], data['destination'], data['departure_date'], data['arrival_date'], data['publicity'], data['budget'],)
        cur.execute(SQL, _data)
        logger.info("%s's journey %s has been putted in database" % (update.message.from_user.username, data['name']))
        #what journey_id does new journey have
        SQL = "SELECT currval('journey_journey_id_seq');"
        cur.execute(SQL)
        journey_id = cur.fetchone()[0]
        #accordance of user and journey
        SQL = "INSERT INTO travelers (journey_id, user_id) VALUES (%s, %s);"
        _data = (journey_id, update.message.from_user.id,)
        cur.execute(SQL, _data)
        logger.info("%s participates in journey %s" % (update.message.from_user.username, data['name']))
        disconnect_from_database(conn)
        update.message.reply_text('Congratulations, journey ' + data['name'] + ' has been created')
    except Exception as e:
        update.message.reply_text('wrong input, journey ' + data['name'] + ' has not been created')
        logger.info("Exception %s has happened" % e)