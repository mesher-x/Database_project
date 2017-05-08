import connection

def add_stop(bot, update):
    cur = connection.conn.cursor()
    SQL = "UPDATE users SET state = %s WHERE user_id = %s;"
    data = ('/add_stop_destination', update.message.from_user.id)
    cur.execute(SQL, data)
    global stop_info
    stop_info = stop()
    bot.sendMessage(chat_id=update.message.chat_id, text='Where do you want to go?')

class stop:
    def __init__(self):
        pass
    def