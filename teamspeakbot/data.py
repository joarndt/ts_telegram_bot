import pickle

# class that contains necessary data for the Teamspeakbot
# it reads and saves necessary data in files


class Data(object):

    # inits data
    def __init__(self, clean=False):

        # start with no bot data
        if clean:
            self.botData = dict()
            self.userInfo = dict()
        else:
            # create or read Bot Data
            try:
                self.botData = self.readBotData()
            except (OSError, IOError, EOFError) as e:
                self.botData = dict()
                self.writeBotData()

            # create or read user Info
            try:
                self.userInfo = self.readUserInfo()
            except (OSError, IOError, EOFError) as e:
                self.userInfo = dict()
                self.writeUserInfo()

        # gets data for Bot initialization on first start
        if 'token' not in self.botData:
            tmp = raw_input("please enter Telegram Bot Token:").replace("\n", "").replace(" ", "")
            self.botData['token'] = tmp

        if 'auth' not in self.botData:
            tmp = raw_input("please enter ClientQuery API Key:").replace("\n", "").replace(" ", "")
            self.botData['auth'] = tmp

        if 'chatId' not in self.botData:
            print "please write in Telegram to get the chat which should be used"

    # reads user info from file
    def readUserInfo(self):
        with open("clientInfo.pkl", "rb") as fp:
            return pickle.load(fp)

    # writes user info into files
    def writeUserInfo(self):
        with open("clientInfo.pkl", "wb") as fp:
            pickle.dump(self.userInfo, fp)

    # reads bot data from file
    def readBotData(self):
        with open("data.pkl", "rb") as fp:
            return pickle.load(fp)

    # write bot data from file
    def writeBotData(self):
        with open("data.pkl", "wb") as fp:
            return pickle.dump(self.botData, fp)

    # check if its a known user
    def isUser(self, uid):
        return uid in self.userInfo

    # getter and setter

    # returns userinfo
    def getUserInfo(self):
        return self.userInfo

    # returns username
    def getUsername(self, id):
        return self.userInfo[id][1]

    # set username persistently
    def setUsername(self, uid, username):
        self.userInfo[uid] = (self.userInfo[uid][0] if uid in self.userInfo else "[color=#aaaaaa]", username)
        self.writeUserInfo()

    # returns usercolor
    def getUsercolor(self, id):
        return self.userInfo[id][0]

    # set usercolor persistently
    def setUsercolor(self, uid, usercolor, username):
        # checks if its a valid hex RGB code
        if len(usercolor) == 6:
            for part in usercolor:
                number = ord(part)
                if (number < 48 or number > 57) and (number < 97 or number > 102):
                    self.writeTelegram("its not a valid Hex RGB code")
                    return False

        self.userInfo[uid] = ("[color=#" + usercolor + "]", username)
        self.writeUserInfo()
        return True

    # returns bot data
    def getBotData(self):
        return self.botData

    # returns bot token
    def getToken(self):
        return self.botData['token']

    # returns ts-api-key
    def getAuth(self):
        return self.botData['auth']

    # returns chat id
    def getChatId(self):
        return self.botData['chatId'] if 'chatId' in self.botData else "0"

    # sets chat id persistently
    def setChatId(self, id):
        self.botData['chatId'] = id
        self.writeBotData()
