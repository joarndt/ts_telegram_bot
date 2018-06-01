
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
            self.celebration = "CAADAgADNQIAAhOqqAc2YWgCd29ZcwI"

    def getCelebration(self):
        return self.celebration
