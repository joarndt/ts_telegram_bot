# -*- coding: iso-8859-1 -*-
from datetime import datetime
from os import listdir
import src.quote as quote
import src.birthday as birthday
import threading
import time
import urllib2
import re
import telepot
from telepot.loop import MessageLoop
from operator import sub
import src.tsclient.tsclient as ts
import logging
import subprocess


# Telegram bot class

logging.basicConfig(filename="log/bot.log", level=logging.DEBUG)

class Bot(object):

    # init
    def __init__(self, data, debug=False):

        #url checking regex
        self.urlRegex = re.compile("^((https?://)?[\w.-]+(?:\.[\w.-]+)+[\w\-._~:/?#[\]@!$&'()*+,;=.]+$)")

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

        if 'sticker' in msg and chat_id == self.adminId:
            self.bot.sendMessage(self.adminId, msg['sticker']['file_id'])

        # checks for textmessage
        if 'text' in msg:

            args = msg['text'].split(' ')
            com = msg['text'].split(' ')[0].split('@')[0]

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
                if com == '/kill':
                    time.sleep(1)
                    subprocess.Popen(['killall', 'ts3client_linux_amd64'], stdout=subprocess.PIPE)
                    subprocess.Popen(['killall', 'python', 'python2.7', 'python2'], stdout=subprocess.PIPE)
                elif com == '/yt':
                    self.youtubeCut(args)
                else:
                    self.handleLinks(self.otherId, msg)

            # Handle other chats
            elif chat_id == self.otherId:

                if com == '/quotes':
                    if len(args) == 2 and self.isNumber(args[1]):
                        self.printQuotes(self.data.readQuotes(), int(args[1]))
                    elif len(args) == 1:
                        self.printQuotes(self.data.readQuotes())
                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /quotes YEAR")

                elif com == '/addquote':
                    if len(args) > 3 and self.isNumber(args[1]):
                        tosend = msg['text'].replace(" ".join(args[:3]) + " ", '')
                        newquote = quote.Quote(args[2], tosend, int(args[1]))
                        self.data.addQuote(newquote)
                        self.bot.sendMessage(chat_id, '"' + str(newquote) + '"' + " added")

                    elif len(args) >= 3 and not self.isNumber(args[1]):
                        tosend = msg['text'].replace(" ".join(args[:2]) + ' ', '')
                        newquote = quote.Quote(args[1], tosend)
                        self.data.addQuote(newquote)
                        self.bot.sendMessage(chat_id, '"' + str(newquote) + '"' + " added")

                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /addquote YEAR(optional) NAME QUOTE")

                elif com == '/deletequote':
                    quotes = self.data.readQuotes()
                    if len(args) == 1:
                        self.printQuotes(quotes, numbers=True)
                        self.bot.sendMessage(chat_id, "Use following syntax /deletequote QUOTE_ID")

                    elif len(args) == 2:
                        part = self.data.deleteQuote(args[1])
                        if part is None:
                            self.bot.sendMessage(chat_id, "Quote not found")
                        else:
                            self.bot.sendMessage(chat_id, str(part) + "\nwas removed")
                    else:
                        self.bot.sendMessage(chat_id, "Use following syntax /deletequote QUOTE_ID")
                        self.bot.sendMessage(chat_id, "or /deletequote for a list of Message IDS ")

                if com == '/birthdays':
                    if len(args) == 1:
                        self.printBirthdays(self.data.readBirthdays())
                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /birthdays")

                elif com == '/addbirthday':
                    if len(args) == 5:
                        try:
                            date = datetime(int(args[3]), int(args[2]), int(args[1]))
                            newBirthday = birthday.Birthday(args[4], date)
                            self.data.addBirthday(newBirthday)
                            self.bot.sendMessage(chat_id, '"' + str(newBirthday) + '"' + " added")
                        except:
                            self.bot.sendMessage(chat_id, "only use following syntax: /addbirthday dd mm yyyy NAME")
                    else:
                        self.bot.sendMessage(chat_id, "only use following syntax: /addbirthday dd mm yyyy NAME")

                elif com == '/deletebirthday':
                    birthdays = self.data.readBirthdays()
                    if len(args) == 1:
                        self.printBirthdays(birthdays, numbers=True)
                        self.bot.sendMessage(chat_id, "Use following syntax /deletebirthday BIRTHDAY_ID")

                    elif len(args) == 2:
                        part = self.data.deleteBirthday(args[1])
                        if part is None:
                            self.bot.sendMessage(chat_id, "Birthday not found")
                        else:
                            self.bot.sendMessage(chat_id, str(part) + "\nwas removed")
                    else:
                        self.bot.sendMessage(chat_id, "Use following syntax /deletebirthday BIRTHDAY_ID")
                        self.bot.sendMessage(chat_id, "or /deletebirthday for a list of Message IDS ")
                elif com == '/yt':
                    if len(args) == 4:
                        if "youtube" in args[1] or "youtu.be" in args[1]:
                            regex = re.compile("[0-5][0-9]:[0-5][0-9]")
                            if regex.match(args[2]) and regex.match(args[3]):
                                duration = map(sub, map(int, args[3].split(":")), map(int, args[2].split(":")), )
                                print duration
                                if duration[0] >= 0 and duration[1] >= 0:
                                    durString = str(duration[0]) + ":" + str(duration[1])
                                    print durString
                                    subprocess.call(["./youtube-cut.sh", args[1], args[2], durString], stdout=subprocess.PIPE)
                        self.sendVideo(chat_id, "")


                else:
                    self.handleLinks(self.otherId, msg)


            # handle teamspeakchat
            elif self.groupId != chat_id:
                if com == '/yt':
                    self.youtubeCut(args)
                else:
                    self.handleLinks(self.otherId, msg)


            # quitting teamspeak
            elif com == '/quit':
                self.teamspeak.tsStop()

            # joining teamspeak
            elif com == '/join':
                self.teamspeak.tsStart()

            elif self.teamspeak.getTsRunning():

                # writes command for current channelclients
                if com == '/status':
                    self.teamspeak.sendStatus()

                # set username for current id
                elif com == '/setusername':
                    self.setUsername(user_id, args)

                # set usercolor for current id
                elif com == '/setusercolor':
                    self.setUsercolor(user_id, args, msg)

                # builds textmessages and writes it into teamspeakchat
                else:

                    #regex for filtering unicode smileys
                    regex = re.compile(u'[\W][U][0][0][0][0-f][0-f][0-f][0-f][0-f]')
                    message = regex.sub('', msg['text'].encode('unicode-escape'))

                    for x in message.split(' '):
                        if self.isValidUrl(x):
                            message = message.replace(x, '[URL]' + x + '[/URL]')

                    if message.replace(" ", "") != "":
                        self.teamspeak.writeTeamspeak(
                            self.userFormat
                            + self.getUsernameWithColor(msg)
                            + ': '
                            + self.chatFormat
                            + message.decode('unicode-escape')
                        )


    def youtubeCut(self, args):
        if len(args) >= 4:
            if "youtube" in args[1] or "youtu.be" in args[1]:
                regex = re.compile("[0-5][0-9]:[0-5][0-9]")
                if regex.match(args[2]) and regex.match(args[3]):
                    duration = map(sub, map(int, args[3].split(":")), map(int, args[2].split(":")), )
                    if duration[0] >= 0 and duration[1] >= 0:
                        durString = str(duration[0]) + ":" + str(duration[1])
                        if args > 4 and "audio" in args[4]:
                            subprocess.call(["./youtube-cut.sh", args[1], args[2], durString, "-a"], stdout=subprocess.PIPE)
                        else:
                            subprocess.call(["./youtube-cut.sh", args[1], args[2], durString], stdout=subprocess.PIPE)
            self.sendVideo(self.otherId, "")


    def handleLinks(self, chat_id, msg):
        message = ""
        send = False
        video = False
        for x in msg["text"].split(' '):
            if self.isValidUrl(x):
                if "i.imgur.com" in x and ".gifv" in x:
                    message += x.replace(".gifv", ".mp4") + " "
                    send = True
                elif "redd.it" in x or "reddit.com" in x:
                    text = self.parseUrl(x, "https://[^\"]*DASH_600_K")
                    if text != "": send = True
                    message += text
                elif "gfycat.com" in x:
                    text = self.parseUrl(x, 'og:video:secure_url.*-mobile.mp4', 30)
                    if text != "": send = True
                    message += text
                elif ".webm" in x:
                    self.convert(x)
                    video = True
                else:
                    message += x + " "
            else:
                message += x + " "
        if video:
            if message != "":
                message = self.getUsername(msg) + ": " + message
            self.sendVideo(chat_id, message)
        elif send:
            self.bot.sendMessage(chat_id, message)

    def convert(self, link=""):
        subprocess.call(["./convert.sh", link], stdout=subprocess.PIPE)

    def sendVideo(self, chat_id, caption=""):
        filelist = self.list_files("cache/", "mp4")
        if filelist is not None:
            for x in filelist:
                self.bot.sendVideo(chat_id, open("cache/" + x, 'rb'), caption=caption)
                subprocess.Popen(["rm", "-rf", "cache/" + x], stdout=subprocess.PIPE)
        return

    def isValidUrl(self, url):
        return self.urlRegex.match(url)

    def list_files(self, directory, extension):
        return (f for f in listdir(directory) if f.endswith('.' + extension))

    # print all birthdays trust me
    def printBirthdays(self, birthdays, numbers=False):
        num = lambda x: "#" + str(x[0]) + " " + str(x[1]) + "\n" if numbers else str(x[1]) + "\n"
        string = reduce(lambda x, y: x + y, map(num, enumerate(reduce(lambda x, y: x + y, birthdays.values(), []))), "")
        string += "No birthdays saved yet." if string == "" else ""

        self.bot.sendMessage(self.otherId, string, parse_mode="Markdown")

    # print all Quotes trust me
    def printQuotes(self, quotes, year=None, numbers=False):
        num = lambda x: "#" + str(x[0]) + " " + str(x[1]) + "\n" if numbers else str(x[1]) + "\n"
        qlist = quotes[year] if year is not None and year in quotes else reduce(lambda x, y: x + y, quotes.values(), [])
        string = reduce(lambda x, y: x + y, map(num, enumerate(qlist)), "")
        string += ("Quotes don't exist" + (" in " + str(year) if year is None else ""))if string == "" else ""

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
    def setUsername(self, user_id, args):
        if len(args) == 2:
            self.data.setUsername(user_id, args[1])
            self.writeTelegram("Username set")
        else:
            self.writeTelegram(
                "only use following syntax: /setusername USERNAME")

    # sets usercolor in data Object
    def setUsercolor(self, user_id, args, msg):
        if len(args) == 2:
            if self.data.setUsercolor(user_id, args[1], self.getUsername(msg)):
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

    # parsingUrl with regex
    def parseUrl(self, url, regex, cut=0):
        try:
            regex = re.compile(regex)
            hdr = {'User-Agent': "Telegrambot which converts redditlinks to directlinks"}
            req = urllib2.Request(url, headers=hdr)
            strings = regex.findall(urllib2.urlopen(req).read())
            if len(strings) > 0:
                return strings[0][cut:] + " "
        except Exception:
            self.logger.debug(Exception)
        return ""

