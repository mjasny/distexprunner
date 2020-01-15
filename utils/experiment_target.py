import uuid
import xmlrpc.client
import config

from utils import ExperimentCommandHandler


class ExperimentTarget:
    def __init__(self, proxy, rpc_handler):
        self.__proxy = proxy
        self.__rpc_handler = rpc_handler
    
    def run_cmd(self, cmd, stdout=None, stderr=None):
        cmd_id = str(uuid.uuid4())

        def stdin(line):
            with xmlrpc.client.ServerProxy(self.__proxy) as proxy:
                proxy.cmd_stdin(cmd_id, line)
        handler = ExperimentCommandHandler(stdout, stderr, stdin)

        self.__rpc_handler._add_handler(cmd_id, handler)
        with xmlrpc.client.ServerProxy(self.__proxy) as proxy:
            proxy.run_cmd(cmd_id, cmd, f'http://{config.CLIENT_IP}:{config.CLIENT_PORT}/')
        return handler


