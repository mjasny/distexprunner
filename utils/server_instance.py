import logging
import threading
import time
import os
from utils import ServerProcess


class AutoKiller:
    def __init__(self, timeout):
        self.timeout = timeout * 3600   # hours
        self.interval = self.timeout / 60 # for 1 hour, check every minute
        logging.info(f'Will kill server after {self.timeout} seconds.')
        self.reset()
        self.thread = threading.Thread(target=self.killer)
        self.thread.daemon = True
        self.thread.start()

    def reset(self):
        self.time_left = self.timeout

    def killer(self):
        while self.time_left > 0:
            time.sleep(self.interval)
            self.time_left -= self.interval
        logging.warning('Autokilling server...')
        os.system('kill %d' % os.getpid())


class ServerInstance:
    def __init__(self, auto_kill=None):
        self.__processes = {}
        if auto_kill:
            self.autokiller = AutoKiller(auto_kill)

    def init(self):
        self.cleanup()
        
    def cleanup(self):
        for p in self.__processes.values():
            p.cleanup()
        self.__processes.clear()

        while len(threading.enumerate()) > 1:
            logging.info('Threads still running:')
            for x in threading.enumerate():
                logging.info(x)
            time.sleep(0.5)
        logging.info('Server cleanup complete')

    def run_cmd(self, cmd_id, cmd, env, callback_addr):
        assert(cmd_id not in self.__processes)
        if hasattr(self, 'autokiller'):
            self.autokiller.reset()
        self.__processes[cmd_id] = ServerProcess(cmd_id, cmd, env, callback_addr)


    def cmd_stdin(self, cmd_id, line):
        if cmd_id not in self.__processes:
            return False

        # if isinstance(line, str):
        #     line = line.encode()
        self.__processes[cmd_id].stdin(line)


    def kill_cmd(self, cmd_id):
        if cmd_id not in self.__processes:
            return False
            
        self.__processes[cmd_id].kill()
