import itertools


class ParameterGrid:
    def __init__(self, **kwargs):
        self.__params = kwargs

    def get(self):
        keys = self.__params.keys()
        for values in itertools.product(*self.__params.values()):
            yield dict(zip(keys, values))