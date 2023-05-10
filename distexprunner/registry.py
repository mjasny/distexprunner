import functools
import collections
import inspect
import os

from .server_list import ServerList
from .parameter_grid import ParameterGrid


class ExperimentStore:
    __experiments = []

    @staticmethod
    def get():
        return ExperimentStore.__experiments

    @staticmethod
    def add(*, grp_name, name, servers, func, params, max_restarts, raise_on_rc, run_always):
        ExperimentStore.__experiments.append(
            (grp_name, name, servers, func, params,
             max_restarts, raise_on_rc, run_always)
        )


def reg_exp(servers=None, params=None, max_restarts=0, raise_on_rc=True, run_always=False):
    if not isinstance(servers, ServerList):
        raise Exception('Servers needs to be a ServerList')

    grp_name = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]

    if params:
        if not isinstance(params, ParameterGrid):
            raise Exception('params needs to be a ParameterGrid')

        def decorator_grid(func):
            for p, name in params.get():
                name = func.__name__+'__'+name

                ExperimentStore.add(
                    grp_name=grp_name,
                    name=name,
                    servers=servers,
                    func=func,
                    params=p,
                    max_restarts=max_restarts,
                    raise_on_rc=raise_on_rc,
                    run_always=run_always,
                )
        return decorator_grid

    def decorator(func):
        ExperimentStore.add(
            grp_name=grp_name,
            name=func.__name__,
            servers=servers,
            func=func,
            params={},
            max_restarts=max_restarts,
            raise_on_rc=raise_on_rc,
            run_always=run_always,
        )
    return decorator
