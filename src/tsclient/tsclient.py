# -*- coding: iso-8859-1 -*-
import subprocess
import logging
import threading
import os
import signal
import time
from message import *
from client import *

# Tsclient controll script and Query handling



class Tsclient(object):

    # init Ts client
    def __init__(self, bot, groupId, auth, debug=False):

        # saving variables
        self.debug = debug
        self.auth = auth
        self.bot = bot
        self.groupId = groupId
        self.logger = logging.getLogger('teamspeak3.handler')
        self.client = None
        self.process = None

        # empty clientlist
        self.tsClients = dict()

        # necessary for query handling
        self.quiet = False

        # set default ids
        self.invokerid = "0"
        self.channelid = "0"

        # init message thread
        self.messageThread = self.initMessageThread()

    # listen to Teamspeakchat
    def tsMessageLoop(self):
        while 1:
            if self.getTsRunning():

                # get teamspeak clientquery messages
                messages = self.client.get_messages()
                for message in messages:
                    self.logger.info(message)

                    # outputs teamspeakchat in telegram group
                    if message.command == 'notifytextmessage':
                        if message['invokerid'] != self.invokerid:
                            msg = message['invokername'] + ':\n' + message['msg']
                            msg = msg.replace("[URL]", "").replace("[/URL]", "")
                            self.writeTelegram(msg)

                    # Teamspeakuser changed to this channel
                    elif message.command == "notifyclientmoved":
                        if 'ctid'in message.keys() and message['ctid'] == self.channelid:
                            if 'invokername' in message.keys() and 'clid' in message.keys():
                                self.clientJoined(message['clid'], message['invokername'])
                            else:
                                self.sendStatus(True)

                    # Teamspeakuser changed to another channel
                    elif message.command == "notifyclientmoved":
                        if 'clid'in message.keys() and message['ctid'] != self.channelid:
                            if 'invokername' in message.keys():
                               if message['clid'] in self.tsClients:
                                   self.clientLeft(message['clid'])
                            else:
                                self.sendStatus(True)

                    # Teamspeakuser joined 
                    elif message.command == "notifycliententerview":
                        if 'ctid' in message.keys() and message['ctid'] == self.channelid:
                            if 'client_nickname' in message.keys() and 'clid' in message.keys():
                                self.clientJoined(message['clid'], message['client_nickname'])

                    # Teamspeakuser left            
                    elif message.command == "notifyclientleftview":
                        if 'cfid' in message.keys() and message['cfid'] == self.channelid and 'clid' in message.keys():
                            self.clientLeft(message['clid'])

                    # gets current userid
                    elif message.is_response_to(Command('whoami')):
                        self.invokerid = message['clid']
                        self.channelid = message['cid']
                        self.sendStatus()

                    # status output for telegram group    
                    elif message.is_response():
                        self.processStatus(message)

            time.sleep(1)
    # inits messageThread
    def initMessageThread(self):
        thread = threading.Thread(target=self.tsMessageLoop)
        thread.daemon = True
        thread.start()
        return thread

    # starts Teamspeak
    def tsStart(self):

        # if Teamspeak is already running
        if self.getTsRunning():
            self.writeTelegram("already in Teamspeak")
        else:
            # some output for Telegram
            self.writeTelegram("joining Teamspeak")

            # starts Teamspeak
            self.process = subprocess.Popen(["ts3"], stdout=subprocess.PIPE, preexec_fn=os.setsid)

            # initiate Clientquery connection

            while self.client is None:
                try:
                    client = Client(self.auth)
                    client.subscribe()
                    self.client = client
                except:
                    self.logger.debug("failed to init connection")
                    time.sleep(1)

            # set boolean
            self.sendWhoami()

    # stops Teamspeak
    def tsStop(self):
        if not self.getTsRunning():
            self.writeTelegram("not in Teamspeak")
        else:
            # some output for Telegram
            self.writeTelegram("quitting Teamspeak")

            # close connection and quit Teamspeak
            self.client.close()
            self.client = None
            while self.process.poll() is None:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            time.sleep(30)

    # quits if bot is alone on the server
    def autoQuit(self):
        self.logger.info("autoquit")
        if self.tsClients.__len__() == 1 and self.invokerid in self.tsClients and self.getTsRunning():
            self.tsStop()

    # sends whoami command for verification
    def sendWhoami(self):
        self.client.send_command(Command('whoami'))

    # send status message for channel_id
    def sendStatus(self, quiet=False):
        self.quiet = quiet
        self.client.send_command(Command('channelclientlist cid=' + self.channelid))

    # builds tsclient dictionary so it knows who is on the server currently
    # adds user joined message if somebody isn't tracked yet
    # and builds status message for Telegram if its not a quiet status
    def processStatus(self, message):
        clients = dict()

        # build message for status and appends these Clients to list
        msg = 'Currently Online:'
        for part in message.responses:
            if 'client_nickname' in part.keys() and 'clid' in part.keys():

                # get new user if somebody joined
                if part['clid'] not in self.tsClients and self.tsClients.__len__() > 0:
                    self.writeTelegram(part['client_nickname'] + " joined Teamspeak")

                # build dictionary
                clients[part['clid']] = part['client_nickname']

                # add to message
                msg += '\n' + part['client_nickname']

        self.tsClients.clear()
        self.tsClients = clients

        print msg
        if not self.quiet:
            self.writeTelegram(msg)
        else:
            self.quiet = False

    # clientLeft message and deletes the leaving client from tsclients
    def clientLeft(self, uid):
        if uid in self.tsClients:
            self.writeTelegram(self.tsClients[uid] + " left Teamspeak")
            del self.tsClients[uid]
        else:
            self.writeTelegram("BIade ffs fix me")

    # client joined message and adds the joined client to tsclients
    def clientJoined(self, uid, nickname):
        self.tsClients[uid] = nickname
        self.writeTelegram(nickname + " joined Teamspeak")

    # returns if Teamspeak is runnig
    def getTsRunning(self):
        return self.client is not None

    # write message into Teamspeak chat
    def writeTeamspeak(self, string):
        message = "sendtextmessage targetmode=2 msg=" + string.replace(" ", "\s")
        self.client.send_command(Command(message.encode('utf-8')))

    # write
    def writeTelegram(self, string):
        self.bot.sendMessage(self.groupId, string)
