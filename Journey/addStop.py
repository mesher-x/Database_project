import connection

def add_stop(bot, update):

    bot.sendMessage(chat_id=update.message.chat_id, text='Where do you want to go?')

class stop:
    def __init__(self):
        pass
    def