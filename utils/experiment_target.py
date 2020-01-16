import uuid
import xmlrpc.client
import config

from utils import ExperimentCommandHandler


class ExperimentTarget:
    def __init__(self, proxy, rpc_handler, data):
        self.__proxy = proxy
        self.__rpc_handler = rpc_handler
        self.data = data
    
    def run_cmd(self, cmd, stdout=None, stderr=None):
        cmd_id = str(uuid.uuid4())

        handler = ExperimentCommandHandler(self.__proxy, cmd_id, stdout, stderr)
        self.__rpc_handler._add_handler(cmd_id, handler)

        with xmlrpc.client.ServerProxy(self.__proxy) as proxy:
            proxy.run_cmd(cmd_id, cmd, f'http://{config.CLIENT_IP}:{config.CLIENT_PORT}/')
            
        return handler


