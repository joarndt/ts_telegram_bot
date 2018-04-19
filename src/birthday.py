from datetime import datetime
from sticker import Sticker

class Birthday(object):

    def __init__(self, name, date):
        self.name = name
        self.date = date

    def __str__(self):
        new = datetime(2000,self.date.month,self.date.day)
        return new.strftime("%d %B ") + str(self.date.year) + " - *" + self.name + "*"

    def __eq__(self, date):
        now = datetime.today()
        return date.year == now.year and date.month == now.month and date.day == now.day

    def wishHappyBirthday(self, bot, chat_id):
        bot.sendMessage(chat_id, "Happy Birthday *" + self.name + "*", parse_mode="Markdown")
        bot.sendSticker(chat_id, Sticker.getInstance().getCelebration())

    def setName(self, name):
        self.name = name

    def setDate(self, date):
        self.date = date

    def getName(self):
        return self.name

    def getDate(self):
        return self.date

