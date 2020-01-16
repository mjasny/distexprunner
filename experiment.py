import logging
import config
import threading

from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client

from utils import ExperimentClientInstance, ExperimentTarget


class Server:
    def __init__(self, id, ip, port=config.SERVER_PORT, **kwargs):
        self.id = id
        self.ip = ip
        self.port = port
        self.data = kwargs


class Printer:
    def __init__(self, fmt='{line}', rstrip=False, end=''):
        self.fmt = fmt
        self.rstrip = rstrip
        self.end = end

    def __call__(self, line):
        if self.rstrip:
            line = line.rstrip()
        print(self.fmt.format(line=line), end=self.end)


class Logfile:
    def __init__(self, filename, append=False):
        mode = 'a' if append else 'w'
        self.file = open(filename, mode)

    def __del__(self):
        self.file.close()

    def __call__(self, line):
        self.file.write(line)


class Base:
    SERVERS = []

    def __init__(self):
        self.__init_called = True
        self.__quit = False
        self.proxies = {}


    def run(self):
        if not hasattr(self, '_Base__init_called'):
            raise Exception(f'{self.__class__.__name__} did not call Base.__init__()')

        if len(self.SERVERS) == 0:
            raise Exception(f'{self.__class__.__name__}.SERVERS is empty')

        logging.info(f'Executing: {self.__class__.__name__}')

        self.__init()
        self.__connect()
        self.experiment(self.__target)
        self.__disconnect()

        logging.info(f'Finished: {self.__class__.__name__}')


    def experiment(self):
        raise Exception(f'{self.__class__.__name__}.experiment() not implemented')

    
    def __init(self):
        self.rpc_server = SimpleXMLRPCServer(('0.0.0.0', config.CLIENT_PORT), allow_none=True, logRequests=False)
        self.experiment_client_instance = ExperimentClientInstance()
        self.rpc_server.register_instance(self.experiment_client_instance)

        ip, port = self.rpc_server.server_address
        logging.info(f'Client listening on: {ip}:{port}')
        self.rpc_server_thread = threading.Thread(target=self.rpc_server.serve_forever)
        self.rpc_server_thread.start()


    def __connect(self):
        for server in self.SERVERS:
            self.proxies[server.id] = f'http://{server.ip}:{server.port}/'
            logging.info(f'Connecting to server: {server.ip}:{server.port}')
            try:
                with xmlrpc.client.ServerProxy(self.proxies[server.id]) as proxy:
                    proxy.init()
            except ConnectionRefusedError:
                logging.error(f'Could not connect to: {server.ip}:{server.port}')
                del self.proxies[server.id]


    def __disconnect(self):
        for proxy_addr in self.proxies.values():
            with xmlrpc.client.ServerProxy(proxy_addr) as proxy:
                proxy.cleanup()
        self.proxies.clear()
        self.rpc_server.shutdown()
        self.rpc_server_thread.join()
        self.experiment_client_instance._clear_handlers()
   

    def __target(self, node_id):
        if node_id not in self.proxies:
            raise Exception(f'No connection found to: {node_id}')

        server = next(filter(lambda x: x.id == node_id, self.SERVERS), None)
        if server is None:
            raise Exception(f'No info for node: {node_id}')

        return ExperimentTarget(self.proxies[node_id], self.experiment_client_instance, server)

        