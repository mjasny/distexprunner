import uuid
import xmlrpc.client
import config
import logging

from utils import ExperimentCommandHandler, AttrDict


class ExperimentTarget:
    def __init__(self, proxy, rpc_handler, server):
        self.__proxy = proxy
        self.__rpc_handler = rpc_handler
        self.__server = server
    
    def run_cmd(self, cmd, stdout=None, stderr=None, env={}):
        cmd_id = str(uuid.uuid4())

        handler = ExperimentCommandHandler(self.__proxy, cmd_id, stdout, stderr)
        self.__rpc_handler._add_handler(cmd_id, handler)

        logging.info(f'Running {cmd_id} on {self.__server.id}: {cmd}')

        with xmlrpc.client.ServerProxy(self.__proxy) as proxy:
            proxy.run_cmd(cmd_id, cmd, env, f'http://{config.CLIENT_IP}:{config.CLIENT_PORT}/')
            
        return handler

    def data(self):
        return self.__server.data


