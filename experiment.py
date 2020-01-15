import logging
import config
import threading

from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client

from utils import ExperimentClientInstance, ExperimentTarget, AttrDict



SERVERS = {}

def add_server(id, ip, port=config.SERVER_PORT, **kwargs):
    if id in SERVERS:
        raise Exception(f'Server IDs need to be unique')

    SERVERS[id] = {
        'ip': ip,
        'port': port,
        'data': kwargs
    }

    logging.info(f'Added server: {id} ({ip}:{port})')


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
    def __init__(self):
        self.__init_called = True
        self.__quit = False
        self.proxies = {}
        self.targets = {}

        self.run()


    def run(self):
        if not hasattr(self, '_Base__init_called'):
            raise Exception(f'{self.__class__.__name__} did not call Base.__init__()')

        logging.info(f'Executing: {self.__class__.__name__}')
        self.__init()
        self.__connect()
        self.experiment()
        self.__disconnect()


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
        for id, server in SERVERS.items():
            self.proxies[id] = f'http://{server["ip"]}:{server["port"]}/'
            logging.info(f'Connecting to server: {server["ip"]}:{server["port"]}')
            try:
                with xmlrpc.client.ServerProxy(self.proxies[id]) as proxy:
                    proxy.init()
            except ConnectionRefusedError:
                logging.error(f'Could not connect to: {server["ip"]}:{server["port"]}')
                del self.proxies[id]

    def __disconnect(self):
        for proxy_addr in self.proxies.values():
            with xmlrpc.client.ServerProxy(proxy_addr) as proxy:
                proxy.cleanup()
        self.proxies.clear()
        self.rpc_server.shutdown()
        self.rpc_server_thread.join()
        self.experiment_client_instance._clear_handlers()
   

    def target(self, node_id):
        if node_id not in self.proxies:
            raise Exception(f'No connection found to: {node_id}')
        return ExperimentTarget(self.proxies[node_id], self.experiment_client_instance)


    def info(self, node_id):
        if node_id not in SERVERS:
            raise Exception(f'No info for node: {node_id}')
        return AttrDict(SERVERS[node_id]['data'])