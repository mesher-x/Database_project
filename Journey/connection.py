import psycopg2

def connect_to_database():
    try:
        conn = psycopg2.connect("dbname='postgres' user='postgres' host='localhost' password='postgres'")
        return conn
    except:
        print "I am unable to connect to the database"