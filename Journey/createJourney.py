import connection

def create_journey(bot, update):
    conn = connection.connect_to_database()
    cur = conn.cursor()
    SQL = "UPDATE users SET state = %s WHERE user_id = %s;"
    data = ('/create_journey_name', update.message.from_user.id)
    cur.execute(SQL, data)
    global journey_info
    journey_info = journey()
    bot.sendMessage(chat_id=update.message.chat_id, text='Input journey name')


class journey:
    def __init__(self):
        pass

    def add_name(self, bot, update):
        self.name = update.message.text
        cur = connection.conn.cursor()
        SQL = "UPDATE users SET state = %s WHERE user_id = %s;"
        data = ('/create_journey_departure_place', update.message.from_user.id)
        cur.execute(SQL, data)
        bot.sendMessage(chat_id=update.message.chat_id, text='Input place of departure')

    def add_departure_point(self, bot, update):
        self.departure_point = update.message.text
        cur = connection.conn.cursor()
        SQL = "UPDATE users SET state = %s WHERE user_id = %s;"
        data = ('/create_journey_destination', update.message.from_user.id)
        cur.execute(SQL, data)
        bot.sendMessage(chat_id=update.message.chat_id, text='Input destination')

    def add_destination(self, bot, update):
        self.destination = update.message.text
        cur = connection.conn.cursor()
        SQL = "UPDATE users SET state = %s WHERE user_id = %s;"
        data = ('/create_journey_departure_date', update.message.from_user.id)
        cur.execute(SQL, data)
        bot.sendMessage(chat_id=update.message.chat_id, text='Input departure date(year-month-day, 0 for not stated)')

    def add_departure_date(self, bot, update):
        self.departure_date = update.message.text if update.message.text != '0' else None
        cur = connection.conn.cursor()
        SQL = "UPDATE users SET state = %s WHERE user_id = %s;"
        data = ('/create_journey_arrival_date', update.message.from_user.id)
        cur.execute(SQL, data)
        bot.sendMessage(chat_id=update.message.chat_id, text='Input arrival date(year-month-day, 0 for not stated)')

    def add_arrival_date(self, bot, update):
        self.arrival_date = update.message.text if update.message.text != '0' else None
        cur = connection.conn.cursor()
        SQL = "UPDATE users SET state = %s WHERE user_id = %s;"
        data = ('/create_journey_budget', update.message.from_user.id)
        cur.execute(SQL, data)
        bot.sendMessage(chat_id=update.message.chat_id, text='Input estimated budget(0 for not stated)')

    def add_budget(self, bot, update):
        self.budget = update.message.text if update.message.text != '0' else None
        cur = connection.conn.cursor()
        SQL = "UPDATE users SET state = %s WHERE user_id = %s;"
        data = ('/create_journey_publicity', update.message.from_user.id)
        cur.execute(SQL, data)
        bot.sendMessage(chat_id=update.message.chat_id, text='Do you want this journey to appear in search results?(y/n)')

    def add_publicity(self, bot, update):
        self.publicity = (update.message.text.lower() == 'y')

    def put_in_database(self, bot, update):
        try:
            cur = connection.conn.cursor()
            #new journey
            SQL = "INSERT INTO journey (journey_name, departure_point, destination, departure_date, arrival_date, is_public, budget) VALUES (%s, %s, %s, %s, %s, %s, %s);"
            data = (self.name, self.departure_point, self.destination, self.departure_date, self.arrival_date, self.publicity, self.budget,)
            cur.execute(SQL, data)
            print 'inserted'
            #what journey_id does new journey have
            SQL = "SELECT currval('journey_journey_id_seq');"
            cur.execute(SQL)
            journey_id = cur.fetchone()[0]
            #accordance of user and journey
            SQL = "INSERT INTO travelers (journey_id, user_id) VALUES (%s, %s);"
            data = (journey_id, update.message.from_user.id,)
            cur.execute(SQL, data)
            print 'travelers'
            #update user state
            SQL = "UPDATE users SET state = %s WHERE user_id = %s;"
            data = ('start', update.message.from_user.id)
            cur.execute(SQL, data)
            bot.sendMessage(chat_id=update.message.chat_id, text='Congratulations, journey ' + self.name + ' is created')
        except Exception as e:
            bot.sendMessage(chat_id=update.message.chat_id, text='wrong input, journey ' + self.name + ' is not created')
            SQL = "UPDATE users SET state = %s WHERE user_id = %s;"
            data = ('start', update.message.from_user.id)
            cur.execute(SQL, data)
            print e

    # def choose_action(self, state, bot, update):
    #     if state == '/create_journey_name':
    #         self.add_name(bot, update)
    #     elif state == '/create_journey_departure_place':
    #         self.add_departure_point(bot, update)
    #     elif state == '/create_journey_destination':
    #         self.add_destination(bot, update)
    #     elif state == '/create_journey_departure_date':
    #         self.add_departure_date(bot, update)
    #     elif state == '/create_journey_arrival_date':
    #         self.add_arrival_date(bot, update)
    #     elif state == '/create_journey_budget':
    #         self.add_budget(bot, update)
    #     elif state == '/create_journey_publicity':
    #         self.add_publicity(bot, update)
    #         self.put_in_database(bot, update)