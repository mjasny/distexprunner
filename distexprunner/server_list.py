import asyncio
import logging
import types

from .server import Server


class ServerList:
    def __init__(self, *servers):
        if not all(isinstance(s, Server) for s in servers):
            raise Exception('Only Server type allowed')

        if len(set(s.id for s in servers)) != len(servers):
            raise Exception('Server IDs must be unique')

        self.__servers = servers
        self.__id_to_server = {s.id: s for s in servers}
        self.__loop = asyncio.get_event_loop()


    def connect_to_all(self):
        if not self.__servers:
            return
        task = asyncio.wait([s._connect() for s in self.__servers])
        self.__loop.run_until_complete(task)


    def disconnect_from_all(self):
        if not self.__servers:
            return
        task = asyncio.wait([s._disconnect() for s in self.__servers])
        self.__loop.run_until_complete(task)


    def wait_cmds_finish(self):
        raise NotImplementedError()


    def __getitem__(self, key):
        if isinstance(key, (int, slice)):
            try:
                return self.__servers[key]
            except IndexError:
                raise Exception(f'IndexError for: {key}')
        elif isinstance(key, str):
            try:
                return self.__id_to_server[key]
            except KeyError:
                raise Exception(f'KeyError for: {key}')
        elif isinstance(key, types.FunctionType):
            return list(filter(key, self.__servers))
        else:
            raise Exception(f'Lookup type: {type(key)} not supported')
        
    def __iter__(self):
        return iter(self.__servers)

    def __len__(self):
        return len(self.__servers)