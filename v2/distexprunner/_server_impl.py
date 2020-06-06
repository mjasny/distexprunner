import asyncio
import logging
import shlex
import os
import sys
import signal

from ._server_interface import ServerInterface
from ._client_interface import ClientInterface
from ._rpc import RPCReader, RPCWriter


class ServerImpl(ServerInterface):
    def __init__(self, reader, writer):
        self.__rpc_reader = RPCReader(reader, writer, self)
        self.rpc = RPCWriter(ClientInterface)(writer)

        self.pings = 0
        self.__processes = {}

        # TODO kill processes if client doesn't respond to ping


    
    async def _on_disconnect(self):
        # logging.info(f'pings={self.pings}')
        for uuid in self.__processes.keys():
            await self.kill_cmd(uuid)

            
    
    async def ping(self, *args, **kwargs):
        # await asyncio.sleep(0.1)
        self.pings += 1
        await self.rpc.pong(*args, **kwargs)

    
    async def run_cmd(self, uuid, cmd, env={}):
        logging.info(f'uuid={uuid} cmd={cmd}')

        async def _read_stream(stream, rpc):
            while True:
                line = await stream.readline()
                if not line:
                    break
                sys.stdout.write(line.decode('utf-8'))
                await rpc(uuid, line.decode('utf-8'))
                
        
        # cmd = ['stdbuf', '-oL'] + shlex.split(cmd)
        # process = await asyncio.create_subprocess_exec(
        #     *cmd,
        #     stdout=asyncio.subprocess.PIPE,
        #     stderr=asyncio.subprocess.PIPE,
        #     stdin=asyncio.subprocess.PIPE
        # )
  
        # TODO environment variables
        # TODO maybe stdbuf necessary

        environ = os.environ.copy()
        environ.update({k: str(v) for k, v in env.items()})

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            env=environ,
            preexec_fn=os.setsid
        )
        self.__processes[uuid] = process

        await asyncio.wait([
            _read_stream(process.stdout, self.rpc.stdout),
            _read_stream(process.stderr, self.rpc.stderr)
        ])
        rc = await process.wait()
        logging.info(f'Got rc={rc} for: {cmd}')
        await self.rpc.rc(uuid, rc)

    
    async def __process_startup(self, uuid):
        waits = 0
        while uuid not in self.__processes:
            await asyncio.sleep(0.1)
            waits += 1
            if waits == 10:
                logging.error(f'{uuid} did never startup')
                return

    async def kill_cmd(self, uuid):
        await self.__process_startup(uuid)

        try:
            os.killpg(os.getpgid(self.__processes[uuid].pid), signal.SIGKILL)
            logging.info(f'killed: {uuid} {self.__processes[uuid].pid}')
        except ProcessLookupError:  #two kills
            pass # TODO maybe send error to client

    
    async def stdin_cmd(self, uuid, line):
        await self.__process_startup(uuid)

        sys.stdout.write(line)
        sys.stdout.flush()

        p = self.__processes[uuid]
        p.stdin.write(line.encode())
        try:
            await p.stdin.drain()
        except ConnectionResetError:
            logging.error(f'ConnectionResetError')