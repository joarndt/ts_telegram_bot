# -*- coding: iso-8859-1 -*-
from datetime import datetime
import threading
import time
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

        self.initTeamspeak(self.data.getChatId())

        print 'I am listening ...'

    # Telegram bot loop
    def handle(self, msg):

        # get chat id
        chat_id = msg['chat']['id']
        user_id = msg['from']['id']

        # checks for textmessage
        if 'text' in msg:

            command = msg['text'].split('@')[0]
            full_command = msg['text'].split(' ')

            # debug output
            self.logger.info(msg)

            if self.groupId == "0":
                self.initTeamspeak(chat_id)

            # do nothing for now
            elif chat_id != self.groupId:
                self.logger.debug("not implemented yet")

            # quitting teamspeak
            elif command == '/quit':
                self.teamspeak.tsQuit()

            # joining teamspeak
            elif command == '/join':
                self.teamspeak.tsStart()

            elif self.teamspeak.getTsRunning():

                # writes command for current channelclients
                if command == '/status':
                    self.teamspeak.sendStatus()

                # unlisten from teamspeakchat
                elif command == '/stfu':
                    self.teamspeak.setListen(False)
                    self.writeTelegram('stopped listening to TS3 Chat')

                # listen to teamspeakchat
                elif command == '/listen':
                    self.teamspeak.setListen(True)
                    self.writeTelegram('started listening to TS3 Chat')

                # set username for current id
                elif command.split(" ")[0] == '/setusername':
                    self.setUsername(user_id, full_command)

                # set usercolor for current id
                elif command.split(" ")[0] == '/setusercolor':
                    self.setUsercolor(user_id, full_command, msg)

                # builds textmessages and writes it into teamspeakchat
                else:

                    #regex for filtering unicode smileys
                    regex = re.compile('[\W][U][0][0][0][0-f][0-f][0-f][0-f][0-f]')
                    message = regex.sub('', msg['text'])

                    if message.replace(" ", "") != "":
                        self.teamspeak.writeTeamspeak(
                            self.userFormat
                            + self.getUsernameWithColor(msg)
                            + ': '
                            + self.chatFormat
                            + message
                        )

#           else:
#               writeTelegram('bot is not in Teamspeak')

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
