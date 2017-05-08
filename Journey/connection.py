import psycopg2
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def connect_to_database():
    try:
        conn = psycopg2.connect("dbname='postgres' user='postgres' host='localhost' password='postgres'")
        return conn
    except:
        logger.info("I am unable to connect to the database")

def disconnect_from_database(conn):
    conn.commit()
    conn.close()
