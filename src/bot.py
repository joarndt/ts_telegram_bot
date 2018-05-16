# -*- coding: iso-8859-1 -*-
from datetime import datetime
import src.quote as quote
import src.birthday as birthday
import threading
import time
import urllib2
import re
import telepot
from telepot.loop import MessageLoop
import src.tsclient.tsclient as ts
import logging
import subprocess

# Telegram bot class

logging.basicConfig(filename="log/bot.log", level=logging.DEBUG)

class Bot(object):

    # init
    def __init__(self, data, debug=False):

        # data and debugging
        self.debug = debug
        self.data = data
        self.logger = logging.getLogger('telegram.bot')

        # Ts Chat Format
        self.userFormat = "[b]"
        self.chatFormat = "[/b][color=grey]"

        # start bot with bot_token
        try:
            self.bot = telepot.Bot(self.data.getToken())
        except Exception as e:
            print e
            print "failed to init Bot"
            print "start with --clean"

        # start messageloop
        MessageLoop(self.bot, self.handle).run_as_thread()
        self.keepAlive()

        # get ids
        self.groupId = self.data.getChatId()
        self.adminId = self.data.getAdminId()
        self.otherId = self.data.getOtherId()
        self.initTeamspeak(self.data.getChatId())

        # send startin message to admin
        if self.adminId != '0':
            self.bot.sendMessage(self.adminId, "Starting...")

        print 'I am listening ...'

    # Telegram bot loop
    def handle(self, msg):

        # get chat id
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']

        # checks for textmessage
        if 'text' in msg:

            command = msg['text'].split(' ')[0].split('@')[0]
            full_command = msg['text'].split(' ')

            # debug output
            self.logger.info(msg)

            # set ids by chat
            if self.groupId == '0' and msg['text'] == 'teamspeak':
                self.initTeamspeak(chat_id)
                self.bot.sendMessage(chat_id, "Teamspeak chat set")

            elif self.adminId == '0' and msg['text'] == 'admin':
                self.adminId = chat_id
                self.data.setAdminId(chat_id)
                self.bot.sendMessage(chat_id, "Admin chat set")

            elif self.otherId == '0' and msg['text'] == 'other':
                self.otherId = chat_id
                self.data.setOtherId(chat_id)
                self.bot.sendMessage(chat_id, "Other chat set")

            # Admin commands
            elif chat_id == self.adminId:
                if command == '/kill':
                    time.sleep(1)
                    subprocess.Popen(['killall', './ts3client_linux_amd64'], stdout=subprocess.PIPE)
                    subprocess.Popen(['killall', 'python', 'python2.7', 'python2'], stdout=subprocess.PIPE)

            # Handle other chats
            elif chat_id == self.otherId:

                if command == '/quotes':
                    if full_command.__len__() == 2 and self.isNumber(full_command[1]):
                        self.printQuotes(self.data.readQuotes(), int(full_command[1]))
                    elif full_command.__len__() == 1:
                        self.printQuotes(self.data.readQuotes())
                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /quotes YEAR")

                elif command == '/addquote':
                    if full_command.__len__() > 3 and self.isNumber(full_command[1]):

                        tosend = msg['text'].replace(" ".join(full_command[:3]) + " ", '')
                        newquote = quote.Quote(full_command[2], tosend, int(full_command[1]))
                        self.data.addQuote(newquote)
                        self.bot.sendMessage(chat_id, '"' + str(newquote) + '"' + " added")
                    elif full_command.__len__() >= 3 and not self.isNumber(full_command[1]):
                        tosend = msg['text'].replace(" ".join(full_command[:2]) + ' ', '')
                        newquote = quote.Quote(full_command[1], tosend)
                        self.data.addQuote(
                            newquote
                        )
                        self.bot.sendMessage(chat_id, '"' + str(newquote) + '"' + " added")
                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /addquote YEAR(optional) NAME QUOTE")

                elif command == '/deletequote':
                    quotes = self.data.readQuotes()
                    if full_command.__len__() == 1:
                        self.printQuotes(quotes, numbers=True)
                        self.bot.sendMessage(chat_id, "Use following syntax /deletequote QUOTE_ID")

                    elif full_command.__len__() == 2:
                        part = self.data.deleteQuote(full_command[1])
                        if part is None:
                            self.bot.sendMessage(chat_id, "Quote not found")
                        else:
                            self.bot.sendMessage(chat_id, str(part) + "\nwas removed")
                    else:
                        self.bot.sendMessage(chat_id, "Use following syntax /deletequote QUOTE_ID")
                        self.bot.sendMessage(chat_id, "or /deletequote for a list of Message IDS ")

                if command == '/birthdays':
                    if full_command.__len__() == 1:
                        self.printBirthdays(self.data.readBirthdays())
                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /birthdays")

                elif command == '/addbirthday':
                    if full_command.__len__() == 5:
                        try:
                            date = datetime(int(full_command[3]), int(full_command[2]), int(full_command[1]))
                            newBirthday = birthday.Birthday(full_command[4], date)
                            self.data.addBirthday(newBirthday)
                            self.bot.sendMessage(chat_id, '"' + str(newBirthday) + '"' + " added")
                        except:
                            self.bot.sendMessage(chat_id, "only use following syntax: /addbirthday dd mm yyyy NAME")
                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /addbirthday dd mm yyyy NAME")

                elif command == '/deletebirthday':
                    birthdays = self.data.readBirthdays()
                    if full_command.__len__() == 1:
                        self.printBirthdays(birthdays, numbers=True)
                        self.bot.sendMessage(chat_id, "Use following syntax /deletebirthday BIRTHDAY_ID")

                    elif full_command.__len__() == 2:
                        part = self.data.deleteBirthday(full_command[1])
                        if part is None:
                            self.bot.sendMessage(chat_id, "Birthday not found")
                        else:
                            self.bot.sendMessage(chat_id, str(part) + "\nwas removed")
                    else:
                        self.bot.sendMessage(chat_id, "Use following syntax /deletebirthday BIRTHDAY_ID")
                        self.bot.sendMessage(chat_id, "or /deletebirthday for a list of Message IDS ")

                else:
                    self.handleLinks(self.otherId, msg['text'])


            # handle teamspeakchat
            elif self.groupId != chat_id:
                self.handleLinks(self.otherId, msg['text'])


            # quitting teamspeak
            elif command == '/quit':
                self.teamspeak.tsStop()

            # joining teamspeak
            elif command == '/join':
                self.teamspeak.tsStart()

            elif self.teamspeak.getTsRunning():

                # writes command for current channelclients
                if command == '/status':
                    self.teamspeak.sendStatus()

                # set username for current id
                elif command == '/setusername':
                    self.setUsername(user_id, full_command)

                # set usercolor for current id
                elif command == '/setusercolor':
                    self.setUsercolor(user_id, full_command, msg)

                # builds textmessages and writes it into teamspeakchat
                else:

                    #regex for filtering unicode smileys
                    regex = re.compile(u'[\W][U][0][0][0][0-f][0-f][0-f][0-f][0-f]')
                    message = regex.sub('', msg['text'].encode('unicode-escape'))

                    if message.replace(" ", "") != "":
                        self.teamspeak.writeTeamspeak(
                            self.userFormat
                            + self.getUsernameWithColor(msg)
                            + ': '
                            + self.chatFormat
                            + message.decode('unicode-escape')
                        )

#           else:
#               writeTelegram('bot is not in Teamspeak')

    def handleLinks(self, chat_id, givenMessage=""):
        message = ""
        send = False
        for x in givenMessage.split(' '):
            if "i.imgur.com" in x and ".gifv" in x:
                message += x.replace(".gifv", ".mp4") + " "
                send = True
            elif "redd.it" in x or "reddit.com" in x:
                text = self.parseUrl(x, 'data-seek-preview.*DASH_600_K', 23)
                if text != "": send = True
                message += text
            elif "gfycat.com" in x:
                text = self.parseUrl(x, 'og:video:secure_url.*-mobile.mp4', 30)
                if text != "": send = True
                message += text
            else:
                message += x + " "

        if send:
            self.bot.sendMessage(chat_id, message)


    # print all birthdays trust me
    def printBirthdays(self, birthdays, numbers=False):
        num = lambda x: "#" + str(x[0]) + " " + str(x[1]) + "\n" if numbers else str(x[1]) + "\n"
        string = reduce(lambda x, y: x + y, map(num, enumerate(reduce(lambda x, y: x + y, birthdays.values(), []))), "")
        self.bot.sendMessage(self.otherId, "No birthdays saved yet." if string == "" else string, parse_mode="Markdown")

    # print all Quotes trust me
    def printQuotes(self, quotes, year=None, numbers=False):

        num = lambda x: "#" + str(x[0]) + " " + str(x[1]) + "\n" if numbers else str(x[1]) + "\n"
        qlist = quotes[year] if year is not None and year in quotes else reduce(lambda x, y: x + y, quotes.values(), [])
        string = reduce(lambda x, y: x + y, map(num, enumerate(qlist)), "")

        if string == "":
            string = "Quotes don't exist"
            if year is None:
                string += " in " + str(year)
        self.bot.sendMessage(self.otherId, string, parse_mode="Markdown")

    def isNumber(self, number):
        try:
            int(number)
            return True
        except ValueError:
            return False

    # init Teamspeak
    def initTeamspeak(self, chatId):
        if not(chatId == "0"):
            self.teamspeak = ts.Tsclient(self.bot, chatId, self.data.getAuth(), self.debug)
        self.groupId = chatId
        self.data.setChatId(chatId)

    # write message into Telegram chat
    def writeTelegram(self, string):
        self.bot.sendMessage(self.groupId, string)

    # thread for keeping the connection
    def __keepAliveThread(self):
        while True:
            try:
                self.bot.getMe()
                now = datetime.today()

                if now.hour == 8 and now.minute == 0:
                    for values in self.data.readBirthdays().itervalues():
                        for part in values:
                            part.wishHappyBirthday(self.bot, self.otherId)

                if not(self.groupId == "0") and int(now.hour) < 18:
                    self.teamspeak.autoQuit()

                if now.hour == 18 and now.minute == 0 and not self.teamspeak.getTsRunning():
                    self.teamspeak.tsStart()

                if now.hour == 13 and now.minute == 37:
                    self.bot.sendMessage(self.otherId, "1337")
                time.sleep(60)

            except Exception:
                self.logger.debug("Thread wanted to die")

    # builds a Thread for keeping the connection alive
    def keepAlive(self):
        t = threading.Thread(target=self.__keepAliveThread)
        t.daemon = True
        t.start()

    # gets username from msg
    def getUsername(self, msg):
        # if known then colorize it and make default name
        if 'id' in msg['from'] and self.data.isUser(msg['from']['id']):
            return self.data.getUsername(msg['from']['id'])
        elif 'username' in msg['from']:
            return msg['from']['username']
        elif 'first_name' in msg['from']:
            return msg['from']['first_name']
        return "no username found"

    # sets username in data Object
    def setUsername(self, user_id, command):
        if command.__len__() == 2:
            self.data.setUsername(user_id, command[1])
            self.writeTelegram("Username set")
        else:
            self.writeTelegram(
                "only use following syntax: /setusername USERNAME")

    # sets usercolor in data Object
    def setUsercolor(self, user_id, command, msg):
        if command.__len__() == 2:
            if self.data.setUsercolor(user_id, command[1], self.getUsername(msg)):
                self.writeTelegram("Usercolor set")
            else:
                self.writeTelegram("This is not a valid Hex RGB code")
        else:
            self.writeTelegram(
                "only use following syntax: /setusercolor ffffff")

    # gets username from msg with color
    def getUsernameWithColor(self, msg):
        # if known then colorize it and make default name
        if 'id' in msg['from'] and self.data.isUser(msg['from']['id']):
            return self.data.getUsercolor(msg['from']['id']) + self.getUsername(msg)
        return self.getUsername(msg)

    def parseUrl(self, url, regex, cut):
        try:
            regex = re.compile(regex)
            strings = regex.findall(urllib2.urlopen(url).read())
            if strings.__len__() > 0:
                return strings[0][cut:] + " "
        except Exception:
            self.logger.debug(Exception)

        return ""

