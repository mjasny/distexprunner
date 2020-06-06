import asyncio
import logging
import collections
import uuid

from ._client_impl import ClientImpl


class Server:
    def __init__(self, id: str, ip: str, port: int=20000, **kwargs):
        self.id = id        # TODO assert types
        self.ip = ip
        self.port = port

        for k, v in kwargs.items():
            if k.startswith('_'):
                raise Exception(f'private/protected attributes not allowed, "{k}" starts with _ or __.')
            if not hasattr(self, k):
                setattr(self, k, v)
            else:
                raise Exception(f'Attribute {k} already exists.')
    

    # def __del__(self):
    #     logging.info('server __del__')


    async def _connect(self):
        self.__reader, self.__writer = await asyncio.open_connection(self.ip, self.port)
        self.__client = ClientImpl(self.__reader, self.__writer)


    async def _disconnect(self):
        self.__writer.close()
        await self.__writer.wait_closed()


    def run_cmd(self, cmd, stdout=None, stderr=None, env={}):
        loop = asyncio.get_event_loop()
        _uuid = str(uuid.uuid4())

        if stdout is not None:
            stdout = stdout if isinstance(stdout, collections.Iterable) else [stdout]
            self.__client._set_stdout(_uuid, stdout)

        if stderr is not None:
            stderr = stderr if isinstance(stderr, collections.Iterable) else [stderr]
            self.__client._set_stderr(_uuid, stderr)

        task = self.__client._run_cmd(_uuid, cmd, env)
        rc_future = loop.run_until_complete(task)
        rpc = self.__client.rpc

        async def kill_task():
            await rpc.kill_cmd(_uuid)
            return await rc_future

        async def stdin_task(line):
            await rpc.stdin_cmd(_uuid, line)


        class Actions:
            def wait(self, block=True):
                if block:
                    return loop.run_until_complete(rc_future)
                
                if not rc_future.done():
                    return None
                return rc_future.result()


            def kill(self):
                return loop.run_until_complete(kill_task())

            def stdin(self, line):
                loop.run_until_complete(stdin_task(line))

            def async_stdin(self, line):
                loop.create_task(rpc.stdin_cmd(_uuid, line))


        return Actions()