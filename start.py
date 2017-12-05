import sys
sys.path.insert(0, '/home/blade/git/ts_telegram_bot/src')
import argparse
import time
from data import *
from bot import *

#parser = argparse.ArgumentParser(description="Process come integers")
#parser.add_argument("-debug",required=False)
#parser.parse_args()


data = Data()
Bot(data, True)

while 1:
    time.sleep(10)
