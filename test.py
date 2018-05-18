from os import listdir


def list_files(self, directory, extension):
    return (f for f in listdir(directory) if f.endswith('.' + extension))


filelist = list_files("~/git/ts_telegram_bot/cache", "mp4")
if filelist is not None:
    for x in filelist:
        print x

