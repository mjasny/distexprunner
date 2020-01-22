import threading
import collections
import xmlrpc.client


class ExperimentCommandHandler:
    def __init__(self, proxy, cmd_id, stdout=[], stderr=[]):
        self.__proxy = proxy
        self.__cmd_id = cmd_id
        self.__stdout = stdout if isinstance(stdout, collections.Iterable) else [stdout]
        self.__stderr = stderr if isinstance(stderr, collections.Iterable) else [stderr]
        self.__rc = None
        self.lock = threading.Lock()
        self.cond = threading.Condition()

    def _cmd_stdout(self, line):
        for handler in self.__stdout:
            handler(line)

    def _cmd_stderr(self, line):
        for handler in self.__stderr:
            handler(line)

    def _cmd_rc(self, rc):
        with self.cond:
            self.__rc = rc 
            self.cond.notifyAll()

    def wait(self):
        with self.cond:
            while self.__rc is None:
                self.cond.wait()
        return self.__rc

    def stdin(self, line):
        with xmlrpc.client.ServerProxy(self.__proxy) as proxy:
            proxy.cmd_stdin(self.__cmd_id, line)

    def kill(self):
        with xmlrpc.client.ServerProxy(self.__proxy) as proxy:
            proxy.kill_cmd(self.__cmd_id)