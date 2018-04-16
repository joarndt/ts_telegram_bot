from datetime import datetime

#class for quote object
class Birthday(object):

    # init Ts client
    def __init__(self, name, date):
        self.name = name
        self.date = date

    def __str__(self):
        new = datetime(2000,self.date.month,self.date.day)
        return new.strftime("%d %B ") + str(self.date.year) + " - *" + self.name + "*"

    def __eq__(self, date):
        return date.year == datetime.today().year \
               and date.month == datetime.today().month \
               and date.day == datetime.today().day

    def greeting(self):
        return "Happy Birthday *" + self.name + "*"

    def setName(self, name):
        self.name = name

    def setDate(self, date):
        self.date = date

    def getName(self):
        return self.name

    def getDate(self):
        return self.date

