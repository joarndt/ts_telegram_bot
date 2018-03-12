# -*- coding: iso-8859-1 -*-
from datetime import datetime
import src.quote as quote
import threading
import time
import urllib2
import re
import telepot
from telepot.loop import MessageLoop
import src.tsclient.tsclient as ts
import logging

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

        print self.data.getToken()

        MessageLoop(self.bot, self.handle).run_as_thread()
        self.keepAlive()

        self.groupId = self.data.getChatId()
        self.adminId = self.data.getAdminId()
        self.otherId = self.data.getOtherId()
        self.initTeamspeak(self.data.getChatId())

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

            elif chat_id == self.adminId:
                if command == '/getStickerSet':
                    if full_command.__len__() == 2:
                        stickers = self.bot.getStickerSet(full_command[1])
                        print stickers['sticker']

                        self.bot.sendSticker(chat_id, stickers['stickers'][0])
                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /setStickerSet NAMEOFSET")
                elif command == '/sendStickerSet':
                    if full_command.__len__() == 2:
                        #self.bot.sendSticker(chat_id, )
                        print "nothing for now"
                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /sendSticker Sticker")



            # Handle other chats
            elif chat_id == self.otherId:

                if command == '/quotes':
                    if full_command.__len__() == 2:
                        self.printQuotes(self.data.readQuotes(), full_command[1])
                    elif full_command.__len__() == 1:
                        self.printQuotes(self.data.readQuotes())
                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /quotes YEAR")

                elif command == '/addQuote':
                    if full_command.__len__() >= 3:
                        self.data.addQuote(quote.Quote(full_command[1],
                                                       msg['text'].replace(full_command[0] + ' ', '')
                                                       .replace(full_command[1] + ' ', '')))
                        self.bot.sendMessage(chat_id, "Quote added")
                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /addQuote NAME QUOTE")

                elif command == '/deleteQuote':
                    quotes = self.data.readQuotes()
                    if full_command.__len__() == 1:
                        string = ""
                        counter = 0
                        for year, quoteList in quotes.items():
                            for part in quoteList:
                                string += str(counter) + part.toString() + "\n"
                                counter += 1
                        self.bot.sendMessage(chat_id, string)
                        self.bot.sendMessage(chat_id, "Use following syntax /deleteQuote QUOTE_ID")

                    elif full_command.__len__() == 2:
                        counter = 0
                        for year, quoteList in quotes.items():
                            for part in quoteList:
                                if str(counter) == full_command[1]:
                                    quotes[year].remove(part)
                                    self.bot.sendMessage(chat_id, part.toString() + "\nwas removed")
                                counter += 1
                    else:
                        self.bot.sendMessage(chat_id, "Use following syntax /deleteQuote QUOTE_ID")
                        self.bot.sendMessage(chat_id, "or /deleteQuote for a list of Message IDS ")

                else:
                    message = ""
                    send = False
                    for x in msg['text'].split(' '):
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

            elif self.groupId != chat_id:
                print "different chat yo"

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

    def printQuotes(self, quotes, year = None):
        string = ""
        if year is None:
            for years, quoteList in quotes.items():
                for part in quoteList:
                    string += part.toString() + "\n"

        elif year in quotes:
            for part in quotes[year]:
                string += part.toString() + "\n"
        else:
            string = "No Quotes in: " + year

        self.bot.sendMessage(self.otherId, string)

    # init Teamspeak
    def initTeamspeak(self, chatId):
        if not(chatId == "0"):
            self.teamspeak = ts.Tsclient(
                 self.bot, chatId, self.data.getAuth(), self.debug)
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
                if not(self.groupId == "0") and datetime.today().hour < 18:
                    self.teamspeak.autoQuit()
                time.sleep(60)

                if datetime.today().hour >= 18 and not self.teamspeak.getTsRunning():
                    self.teamspeak.tsStart()

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
            if self.data.setUsercolor(user_id, command[
                              1], self.getUsername(msg)):
                self.writeTelegram("Usercolor set")
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

