import functools

from .server_list import ServerList
from .parameter_grid import ParameterGrid

EXPERIMENTS = []



def exp_reg(servers=None, params=None):
    if not isinstance(servers, ServerList):
        raise Exception('Servers needs to be a ServerList')

    if params:
        if not isinstance(params, ParameterGrid):
            raise Exception('params needs to be a ParameterGrid')

        def decorator(func):
            for p in params.get():
                name = func.__name__+'_'.join(f'{k}={v}' for k,v in p.items())
                EXPERIMENTS.append((name, servers, functools.partial(func, **p)))
        return decorator


    def decorator(func):
        EXPERIMENTS.append((func.__name__, servers, func))
    return decorator
