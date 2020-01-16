from utils import ServerProcess


class ServerInstance:
    def __init__(self):
        self.__processes = {}

    def init(self):
        self.cleanup()

    def cleanup(self):
        for p in self.__processes.values():
            p.cleanup()
        self.__processes.clear()
        # TODO wait for all threads to terminate

    def run_cmd(self, cmd_id, cmd, callback_addr):
        assert(cmd_id not in self.__processes)
        self.__processes[cmd_id] = ServerProcess(cmd_id, cmd, callback_addr)


    def cmd_stdin(self, cmd_id, line):
        if cmd_id not in self.__processes:
            return False

        if isinstance(line, str):
            line = line.encode()
        self.__processes[cmd_id].stdin(line)


    def kill_cmd(self, cmd_id):
        if cmd_id not in self.__processes:
            return False
            
        self.__processes[cmd_id].kill()
