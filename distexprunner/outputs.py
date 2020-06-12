import sys
import logging
import asyncio


LOG_LEVEL_CMD = 100
logging.addLevelName(LOG_LEVEL_CMD, 'CONSOLE')


class Console:
    def __init__(self, fmt='%s'):
        self.fmt = fmt

    def __call__(self, line):
        logging.log(LOG_LEVEL_CMD, self.fmt % line.rstrip())


class File:
    def __init__(self, filename, append=False, flush=False):
        mode = 'a' if append else 'w'
        self.file = open(filename, mode)
        self.flush = flush

    def __del__(self):
        self.file.close()

    def __call__(self, line):
        self.file.write(line)
        if self.flush:
            self.file.flush()


class SubstrMatcher:
    def __init__(self, substr):
        self.substr = substr
        self.__loop = asyncio.get_event_loop()
        self.__future = self.__loop.create_future()

    def __call__(self, line):
        if self.__future.done():
            return  # TODO maybe make resetable
        if self.substr in line:
            self.__future.set_result(None)

    def wait(self):
        self.__loop.run_until_complete(self.__future)
        return True