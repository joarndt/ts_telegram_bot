from datetime import datetime

#class for quote object
class Quote(object):

    # init Ts client
    def __init__(self, name, date):
        self.name = name
        self.date = date

    def __str__(self):
        return "Happy Birthday *"  + self.name + "*"

    def __eq__(self, date):
        return date.year == datetime.today().year \
               and date.month == datetime.today().month \
               and date.day == datetime.today().day

    def setName(self, name):
        self.name = name

    def setDate(self, date):
        self.date = date

    def getName(self):
        return self.name

    def getDate(self):
        return self.date

