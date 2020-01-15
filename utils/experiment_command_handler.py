import threading

class ExperimentCommandHandler:
    def __init__(self, stdout, stderr, stdin):
        self.__rc = None
        self.__stdout = stdout
        self.__stderr = stderr
        self.__stdin = stdin
        self.lock = threading.Lock()
        self.cond = threading.Condition()

    def _cmd_stdout(self, line):
        if self.__stdout is not None:
            self.__stdout(line)

    def _cmd_stderr(self, line):
        if self.__stderr is not None:
            self.__stderr(line)

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
        self.__stdin(line)