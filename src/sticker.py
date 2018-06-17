import random


class Sticker(object):
    # Here will be the instance stored.
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if Sticker.__instance is None:
            Sticker()
        print "other"
        return Sticker.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if Sticker.__instance is not None:
            raise Exception("This class is a singleton!")
        else:

            Sticker.__instance = self
            self.stickers = dict()
            self.stickers["celebration"] = ["CAADAgADNQIAAhOqqAc2YWgCd29ZcwI", "CAADAgADNAIAAhOqqAfQtrbRnagpMQI"]
            self.stickers["fuckoff"] = ["CAADAgADLAIAAhOqqAdDHCDLDApaWQI"]

    def getSticker(self, string=""):
        if string in self.stickers and self.stickers[string] is not []:
            return self.stickers[string][random.randint(0, len(self.stickers[string]) - 1)]
        return ""

