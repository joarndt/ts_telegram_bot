import argparse
import time
import src.data as mydata
import src.bot as mybot

#parser = argparse.ArgumentParser(description="Process come integers")
#parser.add_argument("-debug",required=False)
#parser.parse_args()


data = mydata.Data()
mybot.Bot(data, True)

while 1:
    time.sleep(10)
