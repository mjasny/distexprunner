import asyncio
import logging

from ._server_impl import ServerImpl


class ExperimentServer:
    def __init__(self, ip, port):
        self.__ip = ip
        self.__port = port


    def start(self):
        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(self.__listen())
        except KeyboardInterrupt:
            logging.info('Closing server')
        finally:
            loop.close()


    async def __listen(self):
        server = await asyncio.start_server(ServerImpl, self.__ip, self.__port)
        addr = server.sockets[0].getsockname()
        logging.info(f'Serving on {addr[0]}:{addr[1]}')

        async with server:
            await server.serve_forever()


  