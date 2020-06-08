import sys
import logging


LOG_LEVEL_CMD = 100
logging.addLevelName(LOG_LEVEL_CMD, 'CONSOLE')


class Console:
    def __init__(self, fmt='%s'):
        self.fmt = fmt

    def __call__(self, line):
        logging.log(LOG_LEVEL_CMD, self.fmt % line.rstrip())


class File:
    def __init__(self, filename, append=False):
        mode = 'a' if append else 'w'
        self.file = open(filename, mode)

    def __del__(self):
        self.file.close()

    def __call__(self, line):
        self.file.write(line)