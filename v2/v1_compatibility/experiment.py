import itertools
import logging

from distexprunner import Server, ServerList, exp_reg


class Base:
    pass


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


class errors:
    class NoConnectionError(Exception):
        pass


class actions:
    class Restart(Exception):
        pass


# TODO use exp_reg


class Proxy:
    def __init__(self, cls):
        self.server_list = ServerList(*cls.SERVERS)
        self.cls = cls
        self.__name__ = cls.__name__

    def __call__(self, servers):
        def target(server):
            if not isinstance(server, Server):
                server = servers[server]
            if not hasattr(server, '_Server__client'): #connection has failed
                raise errors.NoConnectionError
            return server

        while True:
            try:
                self.cls().experiment(target)
                break
            except actions.Restart:
                pass


class factory:
    class Grid:
        def __init__(self, factory_fn, *args):
            for params in itertools.product(*args):
                cls = factory_fn(*params)

                if not issubclass(cls, Base):
                    raise Exception('Factory needs to return a child of experiment.Base')

                suffix = '_'.join(map(str, params))
                cls.__name__ += f'_{suffix}'
                logging.info(f'Generated experiment: {cls.__name__}')

                proxy = Proxy(cls)
                exp_reg(proxy.server_list)(proxy)
