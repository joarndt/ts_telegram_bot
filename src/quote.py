from datetime import datetime

#class for quote object
class Quote(object):

    # init Ts client
    def __init__(self, name, quote, year=datetime.today().year):
        self.name = name
        self.quote = quote
        self.date = datetime(year, datetime.today().month, datetime.today().day)

    def toString(self):
        str(self.date.year) + " - *" + self.name + "*: " + self.quote

    def __str__(self):
        return str(self.date.year) + " - *" + self.name + "*: " + self.quote

    def __add__(self, other=""):
        return self.toString + other

    def setName(self, name):
        self.name = name

    def setQuote(self, quote):
        self.quote = quote

    def setDate(self, date):
        self.date = date

    def getName(self):
        return self.name

    def getQuote(self):
        return self.quote

    def getDate(self):
        return self.date

