import functools
import collections

from .server_list import ServerList
from .parameter_grid import ParameterGrid


class ExperimentStore:
    __experiments = []

    @staticmethod
    def get():
        return ExperimentStore.__experiments

    @staticmethod
    def add(*, name, servers, func, max_restarts):
        ExperimentStore.__experiments.append(
            (name, servers, func, max_restarts)
        )



def reg_exp(servers=None, params=None, max_restarts=0):
    if not isinstance(servers, ServerList):
        raise Exception('Servers needs to be a ServerList')

    if params:
        if not isinstance(params, ParameterGrid):
            raise Exception('params needs to be a ParameterGrid')

        def decorator_grid(func):
            for p in params.get():
                name = func.__name__+'__'+'_'.join(f'{k}={v}' for k,v in p.items())

                ExperimentStore.add(
                    name=name,
                    servers=servers,
                    func=functools.partial(func, **p),
                    max_restarts=max_restarts
                )
        return decorator_grid


    def decorator(func):
        ExperimentStore.add(
            name=func.__name__,
            servers=servers,
            func=func,
            max_restarts=max_restarts
        )
    return decorator