#!/usr/bin/env python3

import argparse
import config
import logging

from xmlrpc.server import SimpleXMLRPCServer

from utils import ServerInstance


class Server:
    def __init__(self, port=config.SERVER_PORT, auto_kill=None):
        self.rpc_server = SimpleXMLRPCServer(('0.0.0.0', port), allow_none=True, logRequests=False)
        self.server_instance = ServerInstance(auto_kill=auto_kill)
        self.rpc_server.register_instance(self.server_instance)


    def start(self):
        ip, port = self.rpc_server.server_address
        logging.info(f'Server listening on: {ip}:{port}')
        self.rpc_server.serve_forever()



if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description='Distributed Experiment Runner Server Instance')
    parser.add_argument('--port', nargs='?', type=int, default=config.SERVER_PORT, help='port for client connection')
    parser.add_argument('--auto-kill', type=float, help='auto terminate server after <int/float> hours')
    args = parser.parse_args()

    logging.basicConfig(format='[%(asctime)s]: %(message)s', level=logging.DEBUG)

    Server(port=args.port, auto_kill=args.auto_kill).start()