import argparse
import time
import src.data as mydata
import src.bot as mybot


# Argument parser
parser = argparse.ArgumentParser()
parser.add_argument("-d",
                    "--debug",
                    required=False,
                    help="enables debugging functionality",
                    action="store_true")
parser.add_argument("-c",
                    "--clean",
                    required=False,
                    help="overwrites all existing files with new ones",
                    action="store_true")
args = parser.parse_args()

#init bot
data = mydata.Data(args.clean)
mybot.Bot(data, args.debug)

while 1:
    time.sleep(10)
