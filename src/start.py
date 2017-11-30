from bot import *
from data import *
import argparse
import time

#parser = argparse.ArgumentParser(description="Process come integers")
#parser.add_argument("-debug",required=False)
#parser.parse_args()


data = Data()
Bot(data, True)

while 1:
    time.sleep(1)
