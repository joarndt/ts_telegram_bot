# -*- coding: iso-8859-1 -*-
import subprocess
import threading
from subprocess import call
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

        # empty clientlist
        self.tsClients = dict()

        # necessary for query handling
        self.listen = True
        self.quiet = False

        # indicates if ts is running
        self.tsRunning = False

        # set default ids
        self.invokerid = "0"
        self.channelid = "0"

        # init message thread
        self.messageThread = self.initMessageThread()

    # listen to Teamspeakchat
    def tsMessageLoop(self):
        while 1:
            if self.tsRunning:

                # get teamspeak clientquery messages
                messages = self.client.get_messages()
                for message in messages:
                    if self.debug: print message

                    # outputs teamspeakchat in telegram group
                    if message.command == 'notifytextmessage':
                        if self.listen and message['invokerid'] != self.invokerid:
                            msg = "_*" + message['invokername'] + ':*_\n' + message['msg']
                            msg = msg.replace("[URL]", "").replace("[/URL]", "")
                            self.writeTelegram(msg)

                    # Teamspeakuser changed to this channel
                    elif message.command == "notifyclientmoved":
                        if 'ctid'in message.keys() and ['ctid'] == self.channelid:
                            self.sendStatus(True)

                    # Teamspeakuser changed to another channel
                    elif message.command == "notifyclientmoved":
                        if 'clid'in message.keys():
                            self.clientLeft(message['clid'])

                    # Teamspeakuser joined 
                    elif message.command == "notifycliententerview":
                        if 'ctid' in message.keys() and ['ctid'] == self.channelid:
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
        if self.tsRunning:
            self.writeTelegram("_*already in Teamspeak*_")

        # some output for Telegram
        self.writeTelegram("_*joining Teamspeak*_")

        # starts Teamspeak
        subprocess.Popen(["ts3"], stdout=subprocess.PIPE)
        time.sleep(20)

        # initiate Clientquery connection
        client = Client(self.auth)
        client.subscribe()
        self.client = client

        # set boolean
        self.setTsRunning(True)
        self.setListen(True)
        self.sendWhoami()

    # stops Teamspeak
    def tsStop(self):

        if not self.tsRunning:
            self.writeTelegram("_*not in Teamspeak*_")
            return

        # some output for Telegram
        self.writeTelegram("_*quitting Teamspeak*_")

        # close connection and quit Teamspeak
        self.setTsRunning(False)
        self.client.close()
        call(["killall","-SIGKILL" , "ts3client_linux_amd64"])
        call(["killall","-SIGKILL" , "ts3client_linux_x86"])
        time.sleep(60);

    # quits Teamspeak
    def tsQuit(self):
        if self.tsRunning:
            self.tsStop()
        else:
            self.writeTelegram('_*Not in Teamspeak*_')

    # quits if bot is alone on the server
    def autoQuit(self):
        print "autoquit"
        if self.tsClients.__len__() == 1 and self.invokerid in self.tsClients and self.tsRunning:
            self.tsQuit()

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
        msg = '_*Currently Online:*_'
        for part in message.responses:
            if 'client_nickname' in part.keys() and 'clid' in part.keys():

                # get new user if somebody joined
                if part['clid'] not in self.tsClients and self.tsClients.__len__() > 0:
                    self.writeTelegram("_*" + part['client_nickname'] + " joined Teamspeak*_")

                # build dictionary
                clients[part['clid']] = part['client_nickname']

                # add to message
                msg += '\n' + part['client_nickname']
        msg += '\nlisten: ' + str(self.listen)

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
            self.writeTelegram("_*" + self.tsClients[uid] + " left Teamspeak*_")
            del self.tsClients[uid]
        else:
            self.writeTelegram("_*BIade ffs fix me*_")

    # client joined message and adds the joined client to tsclients
    def clientJoined(self, uid, nickname):
        self.tsClients[uid] = nickname
        self.writeTelegram("_*" + nickname + " joined Teamspeak*_")

    # returns tsRunning variable
    def getTsRunning(self):
        return self.tsRunning

    # sets tsRunning variable
    def setTsRunning(self, tmp):
        self.tsRunning = tmp

    # sets listen variable
    def setListen(self, tmp):
        self.tsListen = tmp

    # write message into Teamspeak chat
    def writeTeamspeak(self, string):
        message = "sendtextmessage targetmode=2 msg=" + string.replace(" ", "\s")
        self.client.send_command(Command(message.encode('utf-8')))

    # write
    def writeTelegram(self, string):
        self.bot.sendMessage(self.groupId, string)
