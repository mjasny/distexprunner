#!/usr/bin/env python3

import argparse
import config
import logging

from xmlrpc.server import SimpleXMLRPCServer

from utils import ServerInstance


class Server:
    def __init__(self, port=config.SERVER_PORT):
        self.rpc_server = SimpleXMLRPCServer(('0.0.0.0', port), allow_none=True, logRequests=False)
        self.server_instance = ServerInstance()
        self.rpc_server.register_instance(self.server_instance)


    def start(self):
        ip, port = self.rpc_server.server_address
        logging.info(f'Server listening on: {ip}:{port}')
        self.rpc_server.serve_forever()



if __name__ == '__main__': 
    parser = argparse.ArgumentParser(description='Distributed Experiment Runner Server Instance')
    parser.add_argument('--port', nargs='?', type=int, default=config.SERVER_PORT, help='port for client connection')
    args = parser.parse_args()

    logging.basicConfig(format='[%(asctime)s]: %(message)s', level=logging.DEBUG)

    Server(port=args.port).start()